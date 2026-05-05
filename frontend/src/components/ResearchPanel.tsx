"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Download, FolderInput, RefreshCw, Globe,
  FileText, AlertCircle, CheckCircle, Loader2, ArrowRight,
  Link as LinkIcon
} from "lucide-react";
import { cn } from "../lib/utils";

const API_BASE = "http://localhost:8000";

type DownloadFile = {
  filename: string;
  size_kb: number;
  modified_at: string;
};

type ResearchStatus = "idle" | "searching" | "done" | "error";
type SyncStatus = "idle" | "syncing" | "done" | "error";
type ImportStatus = "idle" | "importing" | "done" | "error";

export default function ResearchPanel() {
  const [query, setQuery] = useState("");
  const [maxResults, setMaxResults] = useState(5);
  const [researchStatus, setResearchStatus] = useState<ResearchStatus>("idle");
  const [syncStatus, setSyncStatus] = useState<SyncStatus>("idle");
  const [importStatus, setImportStatus] = useState<ImportStatus>("idle");
  const [urlInput, setUrlInput] = useState("");
  const [downloads, setDownloads] = useState<DownloadFile[]>([]);
  const [message, setMessage] = useState("");
  const [movingFile, setMovingFile] = useState<string | null>(null);

  const fetchDownloads = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/research/downloads`);
      const data = await res.json();
      setDownloads(data.files || []);
    } catch {
      // silently ignore
    }
  };

  useEffect(() => {
    fetchDownloads();
  }, []);

  const handleWebSearch = async () => {
    if (!query.trim()) return;
    setResearchStatus("searching");
    setMessage("");

    try {
      const res = await fetch(`${API_BASE}/api/research/web-search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, max_results: maxResults }),
      });
      const data = await res.json();

      if (res.ok) {
        setResearchStatus("done");
        setMessage(
          data.saved.length > 0 
            ? `调研完成，获取 ${data.saved.length} 篇相关资料`
            : data.warning || "未发现相关资料，请尝试更换关键词"
        );
        fetchDownloads();
      } else {
        setResearchStatus("error");
        setMessage(data.detail || "调研请求失败");
      }
    } catch {
      setResearchStatus("error");
      setMessage("无法连接调研服务，请检查后端状态");
    }
  };

  const handleUrlImport = async () => {
    if (!urlInput.trim() || !urlInput.startsWith("http")) return;
    setImportStatus("importing");
    setMessage("");

    try {
      const res = await fetch(`${API_BASE}/api/research/import-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: urlInput }),
      });
      const data = await res.json();

      if (res.ok) {
        setImportStatus("done");
        setMessage(`成功从 URL 导入: ${data.filename}`);
        setUrlInput("");
        fetchDownloads();
      } else {
        setImportStatus("error");
        setMessage(data.detail || "URL 导入失败");
      }
    } catch {
      setImportStatus("error");
      setMessage("连接失败，请检查网络或后端服务");
    }
    setTimeout(() => setImportStatus("idle"), 3000);
  };

  const handleMoveToUploads = async (filename: string) => {
    setMovingFile(filename);
    try {
      const res = await fetch(`${API_BASE}/api/research/move-to-uploads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename }),
      });
      if (res.ok) {
        setDownloads((prev) => prev.filter((f) => f.filename !== filename));
      }
    } catch {
      // silently ignore
    } finally {
      setMovingFile(null);
    }
  };

  const handleSyncUploads = async () => {
    setSyncStatus("syncing");
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/api/documents/sync-uploads`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok) {
        setSyncStatus("done");
        setMessage(data.message);
      } else {
        setSyncStatus("error");
        setMessage(data.detail || "同步失败");
      }
    } catch {
      setSyncStatus("error");
      setMessage("同步请求超时，请稍后重试");
    }
    setTimeout(() => setSyncStatus("idle"), 4000);
  };

  return (
    <div className="w-full space-y-4">
      {/* ── 一键同步 ── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-5 border border-green-500/10 shadow-lg shadow-green-500/5"
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-green-500/10 text-green-400">
              <FolderInput className="w-5 h-5" />
            </div>
            <div>
              <p className="font-bold text-white text-sm tracking-wide">本地目录增量同步</p>
              <p className="text-[10px] text-gray-500 uppercase mt-0.5 font-medium">
                SOURCE: <code className="text-green-500/80">uploads/</code>
              </p>
            </div>
          </div>
          <button
            onClick={handleSyncUploads}
            disabled={syncStatus === "syncing"}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all duration-300",
              syncStatus === "syncing"
                ? "bg-gray-800 text-gray-500 cursor-not-allowed"
                : "bg-green-600 hover:bg-green-500 text-white shadow-lg shadow-green-600/20 active:scale-95"
            )}
          >
            {syncStatus === "syncing" ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : syncStatus === "done" ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            {syncStatus === "syncing" ? "同步中" : "开始同步"}
          </button>
        </div>
      </motion.div>

      {/* ── 自动化调研 & 导入 ── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="glass rounded-2xl p-5 space-y-5 border border-blue-500/10"
      >
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400">
            <Globe className="w-5 h-5" />
          </div>
          <div>
            <p className="font-bold text-white text-sm tracking-wide">全网自动化调研</p>
            <p className="text-[10px] text-gray-500 uppercase mt-0.5 font-medium">
              POWERED BY <span className="text-blue-400">TAVILY AI</span>
            </p>
          </div>
        </div>

        <div className="space-y-3">
          {/* 搜索框 */}
          <div className="flex gap-2">
            <div className="relative flex-1 group">
              <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-gray-500 group-focus-within:text-blue-400 transition-colors">
                <Search className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleWebSearch()}
                placeholder="输入调研课题..."
                className="w-full bg-black/30 border border-white/5 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
            <select
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="bg-black/30 border border-white/5 rounded-xl px-2 text-[10px] text-gray-400 focus:outline-none"
            >
              {[3, 5, 8].map((n) => (
                <option key={n} value={n}>{n} 篇</option>
              ))}
            </select>
            <button
              onClick={handleWebSearch}
              disabled={researchStatus === "searching" || !query.trim()}
              className={cn(
                "p-2.5 rounded-xl transition-all",
                researchStatus === "searching" || !query.trim()
                  ? "bg-gray-800 text-gray-600"
                  : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20"
              )}
            >
              {researchStatus === "searching" ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <ArrowRight className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* URL 导入框 */}
          <div className="flex gap-2 pt-1 border-t border-white/5">
            <div className="relative flex-1 group">
              <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-gray-500 group-focus-within:text-purple-400 transition-colors">
                <LinkIcon className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleUrlImport()}
                placeholder="粘贴文章链接直接导入..."
                className="w-full bg-black/30 border border-white/5 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50 transition-all"
              />
            </div>
            <button
              onClick={handleUrlImport}
              disabled={importStatus === "importing" || !urlInput.trim().startsWith("http")}
              className={cn(
                "px-3 py-2.5 rounded-xl text-[10px] font-bold transition-all",
                importStatus === "importing" || !urlInput.trim().startsWith("http")
                  ? "bg-gray-800 text-gray-600"
                  : "bg-purple-600/20 hover:bg-purple-600/40 text-purple-400 border border-purple-500/20"
              )}
            >
              {importStatus === "importing" ? "抓取中" : "导入"}
            </button>
          </div>
        </div>

        {/* 状态消息 */}
        <AnimatePresence>
          {message && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className={cn(
                "text-[10px] flex items-center gap-2 font-medium px-3 py-2 rounded-lg",
                researchStatus === "error" || importStatus === "error" || syncStatus === "error"
                  ? "bg-red-500/10 text-red-400 border border-red-500/10"
                  : "bg-blue-500/10 text-blue-400 border border-blue-500/10"
              )}
            >
              {message.includes("失败") ? <AlertCircle className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />}
              {message}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* ── 待筛选资料库 ── */}
      <AnimatePresence>
        {downloads.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl overflow-hidden border border-white/5"
          >
            <div className="flex items-center justify-between px-5 py-4 bg-white/5 border-b border-white/5">
              <div className="flex items-center gap-2">
                <Download className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">待筛选调研成果</span>
              </div>
              <button
                onClick={fetchDownloads}
                className="text-gray-500 hover:text-white transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
            
            <div className="p-3 space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
              {downloads.map((file) => (
                <motion.div
                  key={file.filename}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="group flex items-center gap-3 p-2.5 rounded-xl bg-white/5 border border-white/5 hover:border-amber-500/30 transition-all duration-300"
                >
                  <div className="p-2 rounded-lg bg-black/20 text-gray-400 group-hover:text-amber-400 transition-colors">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] text-white font-medium truncate leading-tight">{file.filename}</p>
                    <p className="text-[9px] text-gray-500 mt-1">{file.size_kb} KB · {file.modified_at}</p>
                  </div>
                  <button
                    onClick={() => handleMoveToUploads(file.filename)}
                    disabled={movingFile === file.filename}
                    className="p-2 rounded-lg bg-amber-500/10 hover:bg-amber-500 text-amber-500 hover:text-black transition-all active:scale-90"
                  >
                    {movingFile === file.filename ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <ArrowRight className="w-3.5 h-3.5" />
                    )}
                  </button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
