import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Voice Agent Platform',
  tagline: 'Open Source Voice AI for Everyone',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://piyush-sahoo.github.io',
  baseUrl: '/Voice-AI-Platform/',

  organizationName: 'Piyush-sahoo',
  projectName: 'Voice-AI-Platform',

  onBrokenLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/Piyush-sahoo/Voice-AI-Platform/tree/main/docs/',
        },
        blog: false, // Disable blog
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    [
      'docusaurus-plugin-openapi-docs',
      {
        id: "api",
        docsPluginId: "classic",
        config: {
          voiceai: {
            specPath: "static/openapi.json",
            outputDir: "docs/api",
            sidebarOptions: {
              groupPathsBy: "tag",
            },
          } satisfies any,
        } satisfies any,
      },
    ],
  ],

  themes: ["docusaurus-theme-openapi-docs"],

  themeConfig: {
    image: 'img/social-card.png',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Voice Agent Platform',
      logo: {
        alt: 'Voice Agent Platform Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          to: '/docs/api',
          label: 'API',
          position: 'left',
        },
        {
          href: 'https://github.com/Piyush-sahoo/Voice-AI-Platform',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Getting Started',
              to: '/docs/intro',
            },
            {
              label: 'API Reference',
              to: '/docs/api',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/Piyush-sahoo/Voice-AI-Platform',
            },
            {
              label: 'Issues',
              href: 'https://github.com/Piyush-sahoo/Voice-AI-Platform/issues',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'Contributing',
              href: 'https://github.com/Piyush-sahoo/Voice-AI-Platform/blob/main/CONTRIBUTING.md',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Voice Agent Platform. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'python', 'json'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
