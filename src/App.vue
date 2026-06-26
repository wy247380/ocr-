<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="header-title">
        <span class="logo-icon">&#x1F4DC;</span>
        <span>专利证书核验系统</span>
      </div>
      <el-menu mode="horizontal" :router="true" :default-active="$route.path" class="nav-menu">
        <el-menu-item index="/">上传核验</el-menu-item>
        <el-menu-item index="/tasks">任务列表</el-menu-item>
        <el-menu-item index="/admin/reviews">人工审核</el-menu-item>
        <el-menu-item index="/admin/audit-log">审计日志</el-menu-item>
        <el-menu-item index="/settings">设置</el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
</script>

<style>
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --bg-color: #f0f4ff;
  --card-radius: 16px;
  --soft-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
}
body { margin: 0; font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; background: var(--bg-color); }
.layout { min-height: 100vh; }
.header {
  display: flex; align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.3);
  padding: 0 24px;
}
.header-title {
  display: flex; align-items: center; gap: 10px;
  font-size: 18px; font-weight: 600; color: #fff;
  min-width: 260px;
}
.logo-icon { font-size: 24px; }
.nav-menu { flex: 1; border-bottom: none; background: transparent; }
.nav-menu .el-menu-item {
  color: rgba(255,255,255,0.85);
  border-bottom: none;
  font-weight: 500;
}
.nav-menu .el-menu-item:hover { color: #fff; background: rgba(255,255,255,0.15); border-radius: 8px; }
.nav-menu .el-menu-item.is-active { color: #fff; background: rgba(255,255,255,0.2); border-radius: 8px; border-bottom: none; }
.main-content { padding: 28px; max-width: 1100px; margin: 0 auto; }
.el-card { border-radius: var(--card-radius); border: none; box-shadow: var(--soft-shadow); }
.el-card__header { border-bottom: 1px solid #f0f0ff; font-weight: 600; color: #4a5568; }
.el-button--primary { background: linear-gradient(135deg, #667eea, #764ba2); border: none; border-radius: 10px; }
.el-button--primary:hover { background: linear-gradient(135deg, #5a6fe0, #6a3f96); }
.el-tag--success { background: #e6f9f0; color: #27ae60; border: none; border-radius: 8px; }
.el-tag--warning { background: #fff7e6; color: #e67e22; border: none; border-radius: 8px; }
.el-tag--danger { background: #fef0f0; color: #e74c3c; border: none; border-radius: 8px; }
.el-tag--info { background: #f0f4ff; color: #667eea; border: none; border-radius: 8px; }
</style>
