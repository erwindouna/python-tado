import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  base: "/python-tado/",
  title: "Tado Async",
  description:
    "Asynchronous Python client for controlling Tado devices, mainly used for Home Assistant",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "Home", link: "/" },
      { text: "Usage", link: "/usage" },
      { text: "API", link: "/api" },
      { text: "Models", link: "/models" },
      { text: "Exceptions", link: "/exceptions" },
    ],

    sidebar: [
      {
        text: "Documentation",
        items: [
          { text: "Home", link: "/" },
          { text: "Usage", link: "/usage" },
          { text: "API Reference", link: "/api" },
          { text: "Models Reference", link: "/models" },
          { text: "Exceptions Reference", link: "/exceptions" },
        ],
      },
    ],

    search: {
      provider: "local",
    },

    socialLinks: [
      {
        icon: "github",
        link: "https://github.com/erwindouna/python-tado",
      },
    ],
  },
});
