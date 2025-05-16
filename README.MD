# Chess Importer

A Dockerized service that imports chess games from Chess.com to Lichess at regular intervals.

## Prerequisites

- Docker
- Docker Compose

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/chess-importer.git
   cd chess-importer
   ```

2. **Configure the service**:
   ```bash
   cp example.config.yaml config.yaml
   ```
   
   Edit the `config.yaml` file with your account details:
   ```yaml
   accounts:
     - name: "your_username"
       chessnut:
         email: "your_chesscom_email@gmail.com"
         password: "your_chesscom_password"
       lichess:
         api_key: "your_lichess_api_token"
       interval_minutes: 1
   
   state_dir: "/app/data"
   ```

   You can add multiple accounts by adding more items to the `accounts` list.

3. **Get a Lichess API token**:
   - Go to https://lichess.org/account/oauth/token
   - Click "Generate a personal token"
   - Copy the token into your config file

## Running the Service

Start the service with Docker Compose:

```bash
docker-compose up --build -d
```

This will:
- Build the Docker image
- Start the container in detached mode
- Automatically restart if the service crashes

## Monitoring

View logs:
```bash
docker-compose logs -f
```

Check running status:
```bash
docker-compose ps
```

## Stopping the Service

```bash
docker-compose down
```

## Data Persistence

Your data is stored in:
- `./data/` - Contains the state files that track imported games
- `./logs/` - Contains application logs

## Configuration Options

| Setting | Description |
|---------|-------------|
| `accounts[].name` | Friendly name for the account |
| `accounts[].chessnut.email` | Chess.com login email |
| `accounts[].chessnut.password` | Chess.com password |
| `accounts[].lichess.api_key` | Lichess API token |
| `accounts[].interval_minutes` | How often to check for new games (minutes) |
| `state_dir` | Where to store state files (don't change this) |

## Troubleshooting

- **Authentication errors**: Verify your Chess.com credentials and Lichess API token
- **Container won't start**: Check logs with `docker-compose logs`
- **Games not importing**: Ensure your Chess.com account has public games or you're using correct credentials

## Security Notes

- Never commit your `config.yaml` to version control
- The `data/` directory contains sensitive state information
- Consider using environment variables for production deployment