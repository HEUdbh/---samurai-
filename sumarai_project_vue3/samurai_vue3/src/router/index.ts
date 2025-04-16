import { createRouter, createWebHistory } from 'vue-router';
import FileUploadVue from '@/components/FileUpload.vue';

// 这里假设 AboutView.vue 存在于 src/views 目录下
// 如果路径不对，需要进行调整

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: FileUploadVue,
        },
    ],
});

// 可以添加全局路由守卫，例如：
router.beforeEach((to, from, next) => {
    // 这里可以添加一些验证逻辑，例如判断用户是否登录等
    next();
});

export default router;
    