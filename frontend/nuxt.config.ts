export default defineNuxtConfig({
  ssr: false,
  compatibilityDate: '2026-09-05',
  devtools: { enabled: false },
  runtimeConfig: {
    public: {
      // This value is embedded into the SPA bundle during `nuxt build`.
      // An empty default keeps the offline LocalStorage mode available.
      apiBase: import.meta.env.NUXT_PUBLIC_API_BASE || '',
    },
  },
  css: ['~/assets/css/main.css'],
  app: {
    head: {
      title: 'VĂN UYỂN - Nơi chữ nghĩa nở hoa',
      htmlAttrs: { lang: 'vi' },
      meta: [
        {
          name: 'description',
          content: 'Khu vườn văn chương: kiến thức, luyện tập và thi thử Ngữ văn.',
        },
      ],
      link: [
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap',
        },
        {
          rel: 'stylesheet',
          href: 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
        },
      ],
    },
  },
})
