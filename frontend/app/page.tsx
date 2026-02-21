import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Hero Section */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex items-center justify-between">
          <div className="text-2xl font-bold text-blue-600">KeywordTracker</div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">登录</Button>
            </Link>
            <Link href="/register">
              <Button>开始免费试用</Button>
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          专业的 Google 关键词追踪工具
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          精准追踪关键词排名，实时监控竞争对手，解放你的 SEO 工作流程
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/register">
            <Button size="lg" className="text-lg px-8">
              免费试用
            </Button>
          </Link>
          <Link href="/pricing">
            <Button variant="outline" size="lg" className="text-lg px-8">
              查看价格
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">核心功能</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              title="多国家追踪"
              description="支持全球 200+ Google 域名，精准定位目标市场"
              icon="🌍"
            />
            <FeatureCard
              title="智能积分制"
              description="按需付费，前100名追踪仅需10积分，灵活高效"
              icon="💰"
            />
            <FeatureCard
              title="实时监控"
              description="自定义追踪间隔，实时掌握排名变化趋势"
              icon="📊"
            />
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">价格方案</h2>
          <p className="text-gray-600 text-center mb-12">灵活定价，总有一款适合你</p>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <PricingCard
              name="基础版"
              price="¥99"
              credits="1,000"
              features={["5-10 关键词", "每日追踪", "Email 支持"]}
              popular={false}
            />
            <PricingCard
              name="专业版"
              price="¥399"
              credits="5,000"
              features={["20-50 关键词", "每小时追踪", "优先支持", "API 访问"]}
              popular={true}
            />
            <PricingCard
              name="企业版"
              price="¥999"
              credits="15,000"
              features={["无限关键词", "实时追踪", "专属客服", "定制报告"]}
              popular={false}
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="container mx-auto px-4 text-center">
          <p>© 2026 KeywordTracker. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 text-center">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function PricingCard({
  name,
  price,
  credits,
  features,
  popular,
}: {
  name: string;
  price: string;
  credits: string;
  features: string[];
  popular: boolean;
}) {
  return (
    <div
      className={`p-8 rounded-xl border-2 ${
        popular ? "border-blue-500 bg-blue-50" : "border-gray-200"
      }`}
    >
      {popular && (
        <span className="bg-blue-500 text-white text-xs px-3 py-1 rounded-full">
          最受欢迎
        </span>
      )}
      <h3 className="text-xl font-semibold mt-4">{name}</h3>
      <div className="my-4">
        <span className="text-4xl font-bold">{price}</span>
        <span className="text-gray-500">/月</span>
      </div>
      <p className="text-gray-600 mb-6">{credits} 积分</p>
      <ul className="space-y-2 mb-8">
        {features.map((feature) => (
          <li key={feature} className="flex items-center gap-2">
            <span className="text-green-500">✓</span>
            {feature}
          </li>
        ))}
      </ul>
      <Link href="/register" className="block">
        <Button className="w-full" variant={popular ? "default" : "outline"}>
          立即购买
        </Button>
      </Link>
    </div>
  );
}
