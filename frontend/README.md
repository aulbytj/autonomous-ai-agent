# Autonomous AI Agent Web Interface

This is a web interface for the Autonomous AI Agent system, built with [Next.js](https://nextjs.org) and enhanced with Turbopack for faster development.

## Features

- Submit natural language task requests to the AI agent
- Monitor task progress and status in real-time
- View task history and results
- Responsive design that works on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js 18.x or later
- The Autonomous AI Agent backend running on port 8096

### Running the Development Server

First, install the dependencies:

```bash
npm install
```

Then, run the development server with Turbopack enabled:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the web interface.

### Backend Connection

The web interface connects to the Autonomous AI Agent backend at `http://localhost:8096`. Make sure the backend server is running before using the web interface.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
