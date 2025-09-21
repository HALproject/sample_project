// npm install framer-motion


import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function DemoScreen() {
  const [showOp1, setShowOp1] = useState(true);
  const [showOp2, setShowOp2] = useState(true);

  return (
    <div className="relative w-screen h-screen overflow-hidden">
      {/* 背景 */}
      <img
        src="/assets/オペレーションルーム.png"
        alt="Operation Room"
        className="w-full h-full object-cover"
      />

      {/* 大モニター（結果ページ） */}
      <iframe
        src="/result"
        className="absolute top-[100px] left-[200px] w-[600px] h-[400px] border-none"
        title="Result Monitor"
      />

      {/* 小モニター（本体SPA） */}
      <iframe
        src="/app"
        className="absolute top-[550px] left-[150px] w-[400px] h-[250px] border-none"
        title="App Monitor"
      />

      {/* オペレーター1 */}
      <AnimatePresence>
        {showOp1 && (
          <motion.img
            key="op1"
            src="/assets/ope.svg"
            alt="Operator 1"
            className="absolute bottom-[50px] left-[220px] w-[100px]"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -150 }} // 上方向に大きく移動して退席
            transition={{ duration: 0.7 }}
          />
        )}
      </AnimatePresence>

      {/* オペレーター2 */}
      <AnimatePresence>
        {showOp2 && (
          <motion.img
            key="op2"
            src="/assets/ope.svg"
            alt="Operator 2"
            className="absolute bottom-[30px] left-[500px] w-[100px]"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -150 }}
            transition={{ duration: 0.7 }}
          />
        )}
      </AnimatePresence>

      {/* 操作用ボタン */}
      <div className="absolute bottom-5 right-5 flex space-x-2 bg-white/20 p-2 rounded">
        <button
          onClick={() => setShowOp1((prev) => !prev)}
          className="px-2 py-1 bg-blue-500 text-white rounded"
        >
          Toggle Op1
        </button>
        <button
          onClick={() => setShowOp2((prev) => !prev)}
          className="px-2 py-1 bg-green-500 text-white rounded"
        >
          Toggle Op2
        </button>
      </div>
    </div>
  );
}
