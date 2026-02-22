"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";

interface Keyword {
  id: number;
  project_id: number;
  keyword: string;
  country_code: string;
  language: string;
  tracking_interval_hours: number;
  is_active: boolean;
  results_count: number;
  latest_rank?: number;
  latest_url?: string;
}

interface Project {
  id: number;
  name: string;
  root_domain: string;
  subdomain: string;
}

const COUNTRY_OPTIONS = [
  { code: "com", name: "美国 (Google.com)" },
  { code: "co.uk", name: "英国 (Google.co.uk)" },
  { code: "co.jp", name: "日本 (Google.co.jp)" },
  { code: "com.au", name: "澳大利亚 (Google.com.au)" },
  { code: "com.hk", name: "香港 (Google.com.hk)" },
  { code: "co.in", name: "印度 (Google.co.in)" },
  { code: "de", name: "德国 (Google.de)" },
  { code: "fr", name: "法国 (Google.fr)" },
];

const INTERVAL_OPTIONS = [
  { value: 1, label: "每小时" },
  { value: 6, label: "每6小时" },
  { value: 12, label: "每12小时" },
  { value: 24, label: "每天" },
];

export default function KeywordsPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get("project");

  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    keyword: "",
    country_code: "com",
    language: "en",
    tracking_interval_hours: 24,
  });

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (projectId) {
      const proj = projects.find((p) => p.id === parseInt(projectId));
      if (proj) setSelectedProject(proj);
    }
  }, [projectId, projects]);

  useEffect(() => {
    if (selectedProject) {
      fetchKeywords(selectedProject.id);
    }
  }, [selectedProject]);

  const fetchProjects = async () => {
    try {
      const res = await fetch("/api/projects", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        if (!selectedProject && data.length > 0) {
          const pid = projectId ? parseInt(projectId) : data[0].id;
          setSelectedProject(data.find((p: Project) => p.id === pid) || data[0]);
        }
      }
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchKeywords = async (pid: number) => {
    try {
      const res = await fetch(`/api/projects/${pid}/keywords`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (res.ok) {
        const data = await res.json();
        setKeywords(data);
      }
    } catch (error) {
      console.error("Failed to fetch keywords:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject) return;

    try {
      const res = await fetch(`/api/projects/${selectedProject.id}/keywords`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        setShowForm(false);
        setFormData({ keyword: "", country_code: "com", language: "en", tracking_interval_hours: 24 });
        fetchKeywords(selectedProject.id);
      }
    } catch (error) {
      console.error("Failed to create keyword:", error);
    }
  };

  const deleteKeyword = async (id: number) => {
    if (!confirm("确定要删除这个关键词吗？")) return;
    try {
      const res = await fetch(`/api/projects/keywords/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (res.ok && selectedProject) {
        fetchKeywords(selectedProject.id);
      }
    } catch (error) {
      console.error("Failed to delete keyword:", error);
    }
  };

  const toggleActive = async (id: number, current: boolean) => {
    try {
      const res = await fetch(`/api/projects/keywords/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ is_active: !current }),
      });
      if (res.ok && selectedProject) {
        fetchKeywords(selectedProject.id);
      }
    } catch (error) {
      console.error("Failed to toggle keyword:", error);
    }
  };

  const getTargetUrl = () => {
    if (!selectedProject) return "";
    return selectedProject.subdomain || selectedProject.root_domain;
  };

  if (loading) {
    return <div className="min-h-screen bg-gray-50 flex items-center justify-center">加载中...</div>;
  }

  if (projects.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">请先创建项目</p>
          <a href="/projects" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
            去创建项目
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">关键词管理</h1>
            <select
              value={selectedProject?.id || ""}
              onChange={(e) => {
                const proj = projects.find((p) => p.id === parseInt(e.target.value));
                setSelectedProject(proj || null);
              }}
              className="px-4 py-2 border rounded-lg"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.subdomain || p.root_domain})
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {selectedProject && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              当前项目: <strong>{selectedProject.name}</strong> | 
              追踪目标: <strong>{getTargetUrl()}</strong>
            </p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">添加关键词</h2>
            <button
              onClick={() => setShowForm(!showForm)}
              className="text-blue-600 hover:underline"
            >
              {showForm ? "收起" : "展开"}
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="lg:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    关键词 *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.keyword}
                    onChange={(e) => setFormData({ ...formData, keyword: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="输入要追踪的关键词"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    搜索引擎
                  </label>
                  <select
                    value={formData.country_code}
                    onChange={(e) => setFormData({ ...formData, country_code: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    {COUNTRY_OPTIONS.map((c) => (
                      <option key={c.code} value={c.code}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    追踪频率
                  </label>
                  <select
                    value={formData.tracking_interval_hours}
                    onChange={(e) => setFormData({ ...formData, tracking_interval_hours: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    {INTERVAL_OPTIONS.map((i) => (
                      <option key={i.value} value={i.value}>{i.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <button
                type="submit"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
              >
                添加关键词
              </button>
            </form>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">关键词</th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">目标</th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">地区</th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">频率</th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">最新排名</th>
                <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">状态</th>
                <th className="px-6 py-3 text-right text-sm font-medium text-gray-500">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {keywords.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    暂无关键词，点击上方"展开"添加
                  </td>
                </tr>
              ) : (
                keywords.map((kw) => (
                  <tr key={kw.id} className={!kw.is_active ? "bg-gray-50" : ""}>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{kw.keyword}</div>
                      <div className="text-sm text-gray-500">{kw.results_count} 条记录</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {getTargetUrl()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {COUNTRY_OPTIONS.find((c) => c.code === kw.country_code)?.name || kw.country_code}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {INTERVAL_OPTIONS.find((i) => i.value === kw.tracking_interval_hours)?.label || `${kw.tracking_interval_hours}h`}
                    </td>
                    <td className="px-6 py-4">
                      {kw.latest_rank ? (
                        <span className="font-medium text-green-600">#{kw.latest_rank}</span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => toggleActive(kw.id, kw.is_active)}
                        className={`px-2 py-1 text-xs rounded-full ${
                          kw.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {kw.is_active ? "监控中" : "已暂停"}
                      </button>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => deleteKeyword(kw.id)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
