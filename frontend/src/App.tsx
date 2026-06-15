import { useState, useEffect } from 'react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', label: '🎵 Dashboard' },
    { id: 'advanced', label: '⚙️ Advanced Settings' },
    { id: 'ensemble', label: '🤝 Ensemble Mode' },
    { id: 'models', label: '📥 Model Manager' },
    { id: 'settings', label: '🛠️ General Options' },
  ];

  return (
    <div className="flex h-screen w-full bg-[#1a1a24] text-white">
      {/* Sidebar */}
      <div className="w-64 bg-[#262635] flex flex-col shadow-xl">
        <div className="p-6 text-2xl font-bold border-b border-gray-700 text-center tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
          UVR
        </div>
        <div className="flex-col p-4 space-y-2 flex-grow">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 font-medium ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30'
                  : 'text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="p-4 text-xs text-gray-500 text-center border-t border-gray-700">
          Ultimate Vocal Remover v5.6
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto p-10 bg-gradient-to-br from-[#1a1a24] to-[#12121a]">
        <div className="max-w-4xl mx-auto backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl p-8 shadow-2xl">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'advanced' && <div className="text-2xl font-bold">Advanced Settings (Coming Soon)</div>}
          {activeTab === 'ensemble' && <div className="text-2xl font-bold">Ensemble Mode (Coming Soon)</div>}
          {activeTab === 'models' && <div className="text-2xl font-bold">Model Manager (Coming Soon)</div>}
          {activeTab === 'settings' && <div className="text-2xl font-bold">General Options (Coming Soon)</div>}
        </div>
      </div>
    </div>
  );
}

function Dashboard() {
  const [models, setModels] = useState<string[]>(['Loading models...']);
  const [selectedMethod, setSelectedMethod] = useState('mdx_net');

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/models')
      .then(res => res.json())
      .then(data => {
        if (data && data[selectedMethod]) {
          setModels(data[selectedMethod]);
        }
      })
      .catch(err => console.error("API Error:", err));
  }, [selectedMethod]);

  return (
    <div className="space-y-8 animate-in fade-in zoom-in duration-500">
      <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">
        Separation Dashboard
      </h1>
      
      {/* Input Section */}
      <div className="border-2 border-dashed border-gray-600 rounded-2xl p-12 text-center hover:border-cyan-400 transition-colors cursor-pointer bg-white/5">
        <div className="text-5xl mb-4">📁</div>
        <h3 className="text-xl font-semibold mb-2">Drag & Drop Audio Files</h3>
        <p className="text-gray-400">or click to browse your computer</p>
      </div>

      {/* Basic Settings */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-[#262635] p-6 rounded-xl border border-gray-700">
          <label className="block text-sm text-gray-400 mb-2 font-semibold uppercase tracking-wider">Process Method</label>
          <select 
            value={selectedMethod}
            onChange={(e) => setSelectedMethod(e.target.value)}
            className="w-full bg-[#1a1a24] border border-gray-600 rounded-lg p-3 text-white outline-none focus:border-cyan-400 transition-all">
            <option value="mdx_net">MDX-Net</option>
            <option value="vr_arch">VR Architecture</option>
            <option value="demucs">Demucs</option>
          </select>
        </div>
        
        <div className="bg-[#262635] p-6 rounded-xl border border-gray-700">
          <label className="block text-sm text-gray-400 mb-2 font-semibold uppercase tracking-wider">Select Model</label>
          <select className="w-full bg-[#1a1a24] border border-gray-600 rounded-lg p-3 text-white outline-none focus:border-cyan-400 transition-all">
            {models.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Start Button */}
      <button className="w-full py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-bold text-xl hover:shadow-lg hover:shadow-purple-500/50 transform hover:-translate-y-1 transition-all duration-300">
        Start Processing
      </button>
    </div>
  );
}
