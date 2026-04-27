"use client";

import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, File, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "../lib/utils";

export default function FileUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = (selectedFile: File) => {
    // Only allow pdf or markdown/text for this MVP
    if (
      selectedFile.type === "application/pdf" ||
      selectedFile.type === "text/plain" ||
      selectedFile.name.endsWith(".md") ||
      selectedFile.name.endsWith(".txt")
    ) {
      setFile(selectedFile);
      setStatus("idle");
      setMessage("");
    } else {
      setStatus("error");
      setMessage("只支持 PDF 或 TXT/Markdown 文件格式。");
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus("uploading");
    setMessage("正在分析文档并提取向量...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/api/documents/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        setStatus("success");
        setMessage("文档已成功解析并存入知识库！");
        // Reset file after a delay
        setTimeout(() => {
          setFile(null);
          setStatus("idle");
        }, 3000);
      } else {
        const errorData = await response.json();
        setStatus("error");
        setMessage(`上传失败: ${errorData.detail || "未知错误"}`);
      }
    } catch (error) {
      setStatus("error");
      setMessage("上传失败，请检查后端服务是否正在运行。");
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto mt-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "glass rounded-3xl p-8 text-center border-2 border-dashed transition-colors duration-300",
          isDragging ? "border-primary bg-primary/10" : "border-border",
          status === "success" && "border-green-500/50 bg-green-500/5",
          status === "error" && "border-red-500/50 bg-red-500/5"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf,.txt,.md"
        />

        <AnimatePresence mode="wait">
          {!file ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-4 py-8"
            >
              <div className="p-4 rounded-full bg-surface">
                <UploadCloud className="w-12 h-12 text-gray-400" />
              </div>
              <div>
                <h3 className="text-xl font-medium text-foreground mb-2">
                  拖拽文件到此处，或 <button onClick={() => fileInputRef.current?.click()} className="text-primary hover:text-primary-hover transition-colors font-semibold">点击浏览</button>
                </h3>
                <p className="text-sm text-gray-400">支持 PDF, TXT, Markdown 格式</p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="file"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="flex flex-col items-center gap-6 py-6"
            >
              <div className="flex items-center gap-4 p-4 glass rounded-2xl w-full max-w-md text-left">
                <div className="p-3 rounded-xl bg-primary/20 text-primary">
                  <File className="w-8 h-8" />
                </div>
                <div className="flex-1 overflow-hidden">
                  <p className="font-medium text-foreground truncate">{file.name}</p>
                  <p className="text-sm text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                {status === "idle" && (
                  <button 
                    onClick={() => setFile(null)}
                    className="text-gray-500 hover:text-red-400 p-2 transition-colors"
                  >
                    ✕
                  </button>
                )}
              </div>

              {status === "idle" && (
                <button
                  onClick={handleUpload}
                  className="px-8 py-3 bg-primary hover:bg-primary-hover text-white rounded-xl font-medium transition-all transform hover:scale-105 shadow-lg shadow-primary/20"
                >
                  上传并解析入库
                </button>
              )}

              {status === "uploading" && (
                <div className="flex flex-col items-center gap-3 text-primary">
                  <Loader2 className="w-8 h-8 animate-spin" />
                  <p className="text-sm font-medium animate-pulse">{message}</p>
                </div>
              )}

              {status === "success" && (
                <div className="flex flex-col items-center gap-3 text-green-400">
                  <CheckCircle className="w-12 h-12" />
                  <p className="font-medium">{message}</p>
                </div>
              )}

              {status === "error" && (
                <div className="flex flex-col items-center gap-3 text-red-400">
                  <AlertCircle className="w-10 h-10" />
                  <p className="font-medium">{message}</p>
                  <button 
                    onClick={() => setStatus("idle")}
                    className="mt-2 text-sm underline hover:text-red-300"
                  >
                    重试
                  </button>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
