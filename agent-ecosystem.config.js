module.exports = {
  apps: [
    {
      name: "yuna-gateway",
      script: "/home/ubuntu/.local/bin/hermes",
      args: "gateway run --profile yuna",
      cwd: "/home/ubuntu/.hermes",
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      env: {
        HERMES_HOME: "/home/ubuntu/.hermes"
      }
    },
    {
      name: "soyu-gateway",
      script: "/home/ubuntu/.local/bin/hermes",
      args: "gateway run --profile soyu",
      cwd: "/home/ubuntu/.hermes",
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      env: {
        HERMES_HOME: "/home/ubuntu/.hermes"
      }
    },
    {
      name: "yerin-gateway",
      script: "/home/ubuntu/.local/bin/hermes",
      args: "gateway run --profile yerin",
      cwd: "/home/ubuntu/.hermes",
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      env: {
        HERMES_HOME: "/home/ubuntu/.hermes"
      }
    },
    {
      name: "haeri-gateway",
      script: "/home/ubuntu/.local/bin/hermes",
      args: "gateway run --profile haeri",
      cwd: "/home/ubuntu/.hermes",
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      env: {
        HERMES_HOME: "/home/ubuntu/.hermes"
      }
    }
  ]
};
