const siteUrl = (import.meta.env.NUXT_PUBLIC_SITE_URL || 'https://nguvancohang.com').replace(/\/$/, '')
const siteTitle = 'VĂN UYỂN - Nơi chữ nghĩa nở hoa'
const siteDescription =
  'Khu vườn văn chương: kiến thức, luyện tập và thi thử Ngữ văn, có chấm bài và nhận xét chi tiết.'

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
      title: siteTitle,
      htmlAttrs: { lang: 'vi' },
      meta: [
        { name: 'description', content: siteDescription },
        { name: 'theme-color', content: '#c3a6cb' },
        // Link previews (Facebook, Zalo, Messenger, X) read these from the
        // static index.html, so URLs must be absolute.
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: 'VĂN UYỂN' },
        { property: 'og:locale', content: 'vi_VN' },
        { property: 'og:url', content: `${siteUrl}/` },
        { property: 'og:title', content: siteTitle },
        { property: 'og:description', content: siteDescription },
        { property: 'og:image', content: `${siteUrl}/og-image.jpg` },
        { property: 'og:image:width', content: '1200' },
        { property: 'og:image:height', content: '630' },
        { property: 'og:image:alt', content: 'VĂN UYỂN - Nơi chữ nghĩa nở hoa' },
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:title', content: siteTitle },
        { name: 'twitter:description', content: siteDescription },
        { name: 'twitter:image', content: `${siteUrl}/og-image.jpg` },
      ],
      link: [
        { rel: 'icon', type: 'image/png', sizes: '48x48', href: '/favicon-48.png' },
        { rel: 'icon', type: 'image/png', sizes: '192x192', href: '/icon-192.png' },
        { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' },
        { rel: 'canonical', href: `${siteUrl}/` },
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
