import FileUpload from "@/components/FileUpload";
import ChatInterface from "@/components/ChatInterface";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center pt-28 pb-20 px-4 relative overflow-hidden">
      {/* Abstract background blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-blue-600/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-600/20 blur-[120px] pointer-events-none" />
      
      <div className="z-10 w-full max-w-7xl">
        <div className="text-center mb-12">
          <div className="inline-block px-4 py-1.5 rounded-full glass mb-4">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent font-medium text-sm tracking-wider uppercase">
              DeepSeek + Ollama RAG
            </span>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
            企业级智能知识库
          </h1>
          
          <p className="text-gray-400 max-w-2xl mx-auto">
            基于本地向量模型和顶级生成式 AI。将您的企业文档转化为智能资产，实现精准语义检索。
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start w-full">
          <div className="flex flex-col">
            <h2 className="text-xl font-semibold mb-2 ml-4 text-white flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-sm">1</span>
              知识库录入
            </h2>
            <FileUpload />
          </div>
          
          <div className="flex flex-col">
            <h2 className="text-xl font-semibold mb-2 ml-4 text-white flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-sm">2</span>
              智能问答检索
            </h2>
            <ChatInterface />
          </div>
        </div>
      </div>
    </main>
  );
}
