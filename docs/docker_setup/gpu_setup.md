# GPU Setup

This page documents the Docker-oriented GPU setup patterns for the AI Evaluation Tool.

The key goal is to make both of these endpoints reachable from `app-cli`:

- `OLLAMA_URL`
- `GPU_URL`

Once those two endpoints are reachable from inside the container, the rest of the evaluation flow stays almost the same. The main difference between local and remote GPU setups is simply where Ollama and the Sarvam AI service are hosted and how Docker reaches them.

## Required Models

The README identifies these primary models for the LLM-as-judge and supporting evaluation flow:

1. `sarvamai/sarvam-2b-v0.5`
2. `google/shieldgemma-2b`
3. `sarvamai/sarvam-translate`
4. `qwen3:32b`

## Local GPU Setup

Use this setup when the Docker machine and the GPU machine are the same host.

This is the simplest and most direct arrangement. Ollama runs normally on the host machine, while Sarvam AI is started from a Docker container built from this repository.

### Serve Ollama On The Host

Start by making sure the judge model is available through Ollama on the host system.

```bash
ollama pull qwen3:32b
ollama serve
```

### Build The CLI Image

The simplest way to run Sarvam AI in a container from this repository is to build the CLI image:

```bash
docker build -f Dockerfile.app-cli -t aiet-app-cli .
```

### Run Sarvam AI In A Docker Container

Run the Sarvam AI service from the `app-cli` image and publish its port to the host:

```bash
docker run --rm -it \
  -p 16000:16000 \
  --add-host host.docker.internal:host-gateway \
  --env-file .env \
  -v "$PWD":/app \
  -w /app \
  aiet-app-cli \
  python src/app/sarvam_ai/main.py --port 16000
```

With this approach, the model-serving process stays isolated in a container, but it still remains reachable from the rest of the Docker-based workflow through the published host port.

### Point Dockerized CLI Commands To The Host Endpoints

Set `.env` so `app-cli` can reach the host-served Ollama and the containerized Sarvam AI service:

```env
OLLAMA_URL="http://host.docker.internal:11434/"
GPU_URL="http://host.docker.internal:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
SARVAM_API_KEY=""
OPENAI_API_KEY=""
```

After this is in place, `docker compose run ... app-cli` commands can call both services through `host.docker.internal`.

## Remote GPU Setup

Use this setup when evaluation commands are run locally, but the actual model serving happens on a separate GPU host.

This setup is useful when your local machine is only orchestrating the workflow and a more powerful remote system is doing the model inference work.

### Pull The Code On The Remote GPU Machine

The remote machine needs the repository because Sarvam AI is started from this codebase.

```bash
git clone https://github.com/cerai-iitm/AIEvaluationTool
cd AIEvaluationTool
```

### Build The CLI Image On The Remote GPU Machine

```bash
docker build -f Dockerfile.app-cli -t aiet-app-cli .
```

### Serve Ollama On The Remote GPU Machine

Ollama should also be running on the GPU machine so the judge model is available close to the inference hardware.

```bash
ollama pull qwen3:32b
ollama serve
```

### Run Sarvam AI On The Remote GPU Machine Using The CLI Image

As you requested, this flow uses the repository code on the GPU machine and runs Sarvam AI through the Dockerized CLI environment:

```bash
docker run --rm -it \
  -p 16000:16000 \
  --env-file .env \
  -v "$PWD":/app \
  -w /app \
  aiet-app-cli \
  python src/app/sarvam_ai/main.py --port 16000
```

This keeps the remote setup close to the local Docker workflow, which makes the operating model easier to understand and maintain.

### Forward The Remote Ports To The Local Machine

From your local machine, create SSH tunnels to both the Ollama port and the Sarvam AI port:

```bash
ssh <user>@<remote-gpu-host> \
  -L 21434:localhost:11434 \
  -L 16000:localhost:16000
```

Once those tunnels are active, the forwarded ports behave like local host ports from Docker’s point of view.

### Point Local Docker Containers To The Forwarded Ports

Because `app-cli` reaches host services via `host.docker.internal`, set:

```env
OLLAMA_URL="http://host.docker.internal:21434/"
GPU_URL="http://host.docker.internal:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
SARVAM_API_KEY=""
OPENAI_API_KEY=""
```

## Notes On Reachability

- `OLLAMA_URL` is used by LLM-as-judge and related local-LLM strategies.
- `GPU_URL` is used by strategy modules that call the Sarvam AI or GPU inference API.
- both endpoints must be reachable from inside the `app-cli` container

If either endpoint is wrong, the workflow usually fails later during execution or analysis, so this is a good place to validate connectivity early.

## Additional Models Downloaded During Runtime

The README also notes that these smaller models may be downloaded during execution:

- `amedvedev/bert-tiny-cognitive-bias`
- `LibrAI/longformer-harmful-ro`
- `vectara/hallucination_evaluation_model`
- `thenlper/gte-small`
- `all-MiniLM-L6-v2`
- `nicholasKluge/ToxiGuardrail`
- `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- `google/flan-t5-large`
- `holistic-ai/bias_classifier_albertv2`
- `Human-CentricAI/LLM-Refusal-Classifier`
- `cross-encoder/nli-deberta-base`

## Validation Checklist

- Ollama is reachable
- Sarvam AI is reachable
- `.env` values match the actual ports
- SSH tunneling is active for remote setups
- `app-cli` can resolve `host.docker.internal`

