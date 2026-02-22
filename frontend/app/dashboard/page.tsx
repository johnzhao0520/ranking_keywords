import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">KeywordTracker</h1>
          <div className="flex items-center gap-4">
            <Link href="/projects">
              <Button variant="ghost">项目管理</Button>
            </Link>
            <Link href="/keywords">
              <Button>关键词管理</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-gray-500 text-sm mb-2">项目数</h3>
            <p className="text-3xl font-bold text-gray-900">-</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-gray-500 text-sm mb-2">关键词总数</h3>
            <p className="text-3xl font-bold text-gray-900">-</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-gray-500 text-sm mb-2">剩余积分</h3>
            <p className="text-3xl font-bold text-gray-900">-</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Link href="/projects" className="block">
            <div className="bg-white rounded-lg shadow-md p-8 hover:shadow-lg transition-shadow cursor-pointer">
              <h2 className="text-xl font-semibold mb-2">项目管理</h2>
              <p className="text-gray-600">创建和管理您的SEO项目，设置域名信息</p>
            </div>
          </Link>
          <Link href="/keywords" className="block">
            <div className="bg-white rounded-lg shadow-md p-8 hover:shadow-lg transition-shadow cursor-pointer">
              <h2 className="text-xl font-semibold mb-2">关键词管理</h2>
              <p className="text-gray-600">添加和追踪关键词排名</p>
            </div>
          </Link>
        </div>
      </main>
    </div>
  );
}
