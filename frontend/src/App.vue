<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header class="header">
    <div class="header-inner">
      <RouterLink to="/" class="logo">We Split</RouterLink>
      <nav class="nav">
        <RouterLink to="/" class="nav-link">События</RouterLink>
        <RouterLink to="/users" class="nav-link">Люди</RouterLink>
      </nav>
    </div>
  </header>

  <RouterView />
</template>

<style scoped>
.header {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1080px;
  margin: 0 auto;
  padding: 14px 24px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
  text-decoration: none;
}

.nav {
  display: flex;
  gap: 4px;
}

.nav-link {
  padding: 6px 12px;
  color: var(--muted);
  text-decoration: none;
  border-radius: var(--radius);
}

.nav-link:hover {
  color: var(--ink);
}

.nav-link.router-link-exact-active {
  color: var(--ink);
  background: var(--bg);
}

@media (max-width: 640px) {
  .header-inner {
    padding: 12px 16px;
  }
}
</style>
