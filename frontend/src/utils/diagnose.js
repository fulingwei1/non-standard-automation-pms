/**
 * 登录问题诊断工具
 * 在浏览器控制台运行 diagnoseLogin() 来检查问题
 */

export function diagnoseLogin() {
  console.log("🔍 开始诊断登录问题...\n");

  const issues = [];
  const warnings = [];
  const info = [];

  // 1. 通过前端代理检查后端服务（避免直接访问 8000 触发 CORS/跨域误判）
  console.log("1️⃣ 检查后端服务（通过前端代理 /api）...");
  fetch("/api/v1/health")
    .then(async (res) => {
      const text = await res.text();
      if (!res.ok) {
        console.error("❌ 后端健康检查失败:", res.status, text);
        issues.push(`后端健康检查失败（通过代理 /api），HTTP ${res.status}`);
        return;
      }
      try {
        const data = JSON.parse(text);
        console.log("✅ 后端服务正常:", data);
      } catch {
        console.log("✅ 后端服务正常（非JSON响应）:", text);
      }
      info.push("后端服务运行正常（通过代理）");
    })
    .catch((err) => {
      console.error("❌ 后端服务无法连接（通过代理）:", err.message);
      issues.push("后端服务未启动或前端代理无法连接后端 (/api -> 127.0.0.1:8000)");
      console.log("\n💡 解决方案: 在项目根目录运行 ./start.sh");
      console.log("   或手动启动后端: python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000");
      console.log("   如果 8000 被占用或不可用，可改端口并设置：VITE_BACKEND_PORT=8001 pnpm dev");
    });

  // 2. 检查登录API端点（同样走代理）
  console.log("\n2️⃣ 检查登录API端点（通过前端代理 /api）...");
  fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: "username=test&password=test",
  })
    .then((res) => {
      if (res.status === 401) {
        console.log("✅ API端点正常 (返回401是预期的，因为用户名密码错误)");
        info.push("登录API端点可访问");
      } else {
        console.warn("⚠️ API返回状态:", res.status);
        warnings.push(`API返回状态: ${res.status}`);
      }
    })
    .catch((err) => {
      console.error("❌ API端点无法访问:", err.message);
      issues.push("登录API端点无法访问");
    });

  // 3. 检查本地存储
  console.log("\n3️⃣ 检查本地存储...");
  const token = localStorage.getItem("token");
  if (token) {
    console.log("ℹ️ 发现已保存的token:", token.substring(0, 20) + "...");
    warnings.push("检测到已保存的token，可能需要清除");
  } else {
    console.log("✅ 本地存储正常（无token）");
    info.push("本地存储正常");
  }

  // 4. 检查网络代理
  console.log("\n4️⃣ 检查前端代理配置...");
  const currentHost = window.location.host;
  const currentProtocol = window.location.protocol;
  console.log(`当前前端地址: ${currentProtocol}//${currentHost}`);
  info.push(`前端运行在: ${currentHost}`);

  // 5. 检查CORS
  console.log("\n5️⃣ CORS配置检查...");
  console.log("ℹ️ 如果看到CORS错误，请检查后端配置");
  warnings.push("请检查浏览器Network标签中的CORS错误");

  // 汇总
  setTimeout(() => {
    console.log("\n" + "=".repeat(50));
    console.log("📊 诊断结果汇总:");
    console.log("=".repeat(50));

    if (issues.length > 0) {
      console.error("\n❌ 发现的问题:");
      issues.forEach((issue, i) => console.error(`  ${i + 1}. ${issue}`));
    }

    if (warnings.length > 0) {
      console.warn("\n⚠️ 警告:");
      warnings.forEach((warn, i) => console.warn(`  ${i + 1}. ${warn}`));
    }

    if (info.length > 0) {
      console.log("\n✅ 正常项:");
      info.forEach((item, i) => console.log(`  ${i + 1}. ${item}`));
    }

    console.log("\n💡 快速解决方案:");
    console.log("  1. 确保后端服务运行: ./start.sh");
    console.log("  2. 使用演示账户登录（无需后端）");
    console.log("  3. 检查浏览器控制台的Network标签查看请求详情");
    console.log("=".repeat(50));
  }, 2000);
}

// 导出到全局，方便在控制台调用
if (typeof window !== "undefined") {
  window.diagnoseLogin = diagnoseLogin;
}
