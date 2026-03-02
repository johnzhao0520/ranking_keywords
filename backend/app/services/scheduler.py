"""
定时任务服务 - 使用 APScheduler
"""
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal
from app.models.models import Keyword, RankResult, Subscription, CreditTransaction, SubscriptionStatus
from app.services.tracker import google_tracker
import asyncio
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def get_now():
    """获取当前时间（带时区）"""
    return datetime.now(timezone.utc)


async def track_keyword_task(keyword_id: int):
    """追踪单个关键词"""
    db = SessionLocal()
    try:
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword or not keyword.is_active:
            return {"status": "skipped", "reason": "inactive"}
        
        # 获取项目信息
        project = keyword.project
        target_domain = project.subdomain or project.root_domain
        
        # 检查用户积分
        subscription = db.query(Subscription).filter(
            Subscription.user_id == project.user_id,
            Subscription.status == SubscriptionStatus.ACTIVE.value
        ).first()
        
        if not subscription or subscription.credits <= 0:
            return {"status": "skipped", "reason": "no_credits"}
        
        # 追踪关键词
        result = await google_tracker.track_keyword(
            keyword=keyword.keyword,
            country=keyword.country_code,
            language=keyword.language
        )
        
        if not result:
            return {"status": "failed", "reason": "tracking_error"}
        
        # 查找目标域名排名
        results_list = result.get("results", [])
        rank = None
        url = None
        title = None
        snippet = None
        
        # 保存完整 SERP 结果（Top 10）
        import json
        serp_top10 = results_list[:10] if results_list else []
        serp_results_json = json.dumps(serp_top10)
        
        for idx, r in enumerate(results_list, 1):
            if target_domain and target_domain in r.get("domain", ""):
                rank = idx
                url = r.get("link")
                title = r.get("title")
                snippet = r.get("snippet")
                break
        
        # 如果没匹配到目标域名，不记录排名（不在前100名）
        if not rank:
            logger.info(f"关键词 {keyword.keyword} 未在前100名找到目标域名 {target_domain}")
            # 仍记录一次追踪，但 rank 设为 null
            rank = None
            credits_used = 1  # 每次追踪消耗1积分
        
        # 扣除积分
        subscription.credits -= credits_used
        
        # 保存结果
        rank_result = RankResult(
            keyword_id=keyword_id,
            rank=rank,
            url=url,
            title=title,
            snippet=snippet,
            serp_results=serp_results_json,
            credits_used=credits_used
        )
        db.add(rank_result)
        
        # 记录交易
        transaction = CreditTransaction(
            user_id=project.user_id,
            amount=-credits_used,
            transaction_type="consume",
            description=f"Auto-track: {keyword.keyword}"
        )
        db.add(transaction)
        db.commit()
        
        logger.info(f"关键词 {keyword.keyword} 追踪成功，排名: #{rank}")
        return {"status": "success", "rank": rank, "credits_used": credits_used}
        
    except Exception as e:
        db.rollback()
        logger.error(f"关键词追踪失败: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


async def process_due_keywords():
    """处理所有到期的关键词"""
    db = SessionLocal()
    try:
        now = get_now()
        
        # 获取所有活跃关键词
        keywords = db.query(Keyword).filter(
            Keyword.is_active == True
        ).all()
        
        due_count = 0
        
        for kw in keywords:
            interval = kw.tracking_interval_hours or 24
            
            if kw.results:
                # 获取最新结果
                last_result = kw.results[0]
                if last_result.checked_at:
                    next_check = last_result.checked_at + timedelta(hours=interval)
                    if now >= next_check:
                        # 到期，执行追踪
                        await track_keyword_task(kw.id)
                        due_count += 1
            else:
                # 从未追踪，立即追踪
                await track_keyword_task(kw.id)
                due_count += 1
        
        logger.info(f"处理了 {due_count} 个到期关键词")
        return {"status": "success", "due_count": due_count}
        
    finally:
        db.close()


def start_scheduler():
    """启动定时任务调度器"""
    # 每小时检查一次到期关键词
    scheduler.add_job(
        process_due_keywords,
        trigger=IntervalTrigger(hours=1),
        id="process_keywords",
        name="处理到期关键词",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("定时任务调度器已启动")


def stop_scheduler():
    """停止定时任务调度器"""
    scheduler.shutdown()
    logger.info("定时任务调度器已停止")
