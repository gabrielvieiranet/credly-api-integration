# Infrastructure - Terraform

Este diretório contém a infraestrutura como código (IaC) do projeto Credly Ingestion Pipeline usando Terraform.

## Estrutura

```
infra/
├── providers.tf       # Configuração Terraform e Provider AWS
├── variables.tf       # Variáveis de entrada
├── locals.tf          # Valores calculados
├── data.tf            # Data sources
├── main.tf            # Recursos principais (S3, DynamoDB, Lambda, Step Functions)
├── outputs.tf         # Outputs do Terraform
├── override.tf        # LocalStack override (não commitado)
└── terraform.tfvars   # Valores das variáveis (não commitado em produção)
```

## Recursos Criados

### S3 Bucket

- **Nome**: Definido em `terraform.tfvars` (padrão: `my-datalake-bucket`)
- Armazena dados brutos em formato Parquet particionados por data

### Secrets Manager

- **Nome**: Definido em `terraform.tfvars` (padrão: `my-app/credentials`)
- Armazena credenciais da API Credly
- Cria com placeholder, atualizar via `scripts/update_local_token.sh`
- Lifecycle `ignore_changes` evita sobrescrever valores atualizados

### DynamoDB Tables

1. **Metadata Table** (`credly-ingestion-metadata-{env}`)
   - Armazena metadados de todas as tabelas
   - Hash Key: `table_name` (badges_emitidas, badges_templates, etc.)
   - **Atributos para watermarks** (cargas incrementais):
     - `watermark_timestamp` - último timestamp processado
     - `last_updated_at` - data/hora da última atualização
   - **Atributos para hash validation** (templates):
     - `payload_hash` - SHA256 do payload (IDs + updated_at)
     - `ids_array` - array de IDs processados
     - `updated_at_array` - array de timestamps

### Lambda Function

- **Nome**: `credly-ingestion`
- **Runtime**: Python 3.12
- **Timeout**: 900s (15 min)
- **Memory**: 512 MB
- **Handler**: `handlers.credly_ingestion_handler.lambda_handler`

### Step Functions

- **Nome**: `credly-ingestion-orchestrator-{env}`
- **Orquestra**: Chamadas para badges e templates
- **Parâmetros de entrada**:
  - `mode`: "full" ou "incremental"
  - `load_type`: "badges" ou "templates"
  - `start_date`: Data início (opcional)
  - `end_date`: Data fim (opcional)

## Estratégias de Carga

### Badges (Incremental)

1. Lê watermark do DynamoDB
2. Define `updated_at_min = watermark - 10min` (overlap)
3. Define `updated_at_max = now()`
4. Faz paginação até exaurir
5. Atualiza watermark com `max(updated_at)`

### Templates (Hash Validation)

1. Busca todos os templates (~200 registros)
2. Gera hash SHA256 do payload (IDs + updated_at)
3. Compara com hash armazenado no DynamoDB
4. Se diferente: atualiza tabelas completas
5. Se igual: skip (sem mudanças)

## Uso

### Inicializar Terraform

```bash
cd infra
terraform init
```

### Planejar mudanças

```bash
terraform plan
```

### Aplicar infraestrutura

```bash
terraform apply
```

### Destruir infraestrutura

```bash
terraform destroy
```

## LocalStack (Desenvolvimento)

Para configurar a infraestrutura localmente com LocalStack, execute:

```bash
./scripts/setup_infra.sh
```

Este script:
1. Limpa recursos existentes (S3, DynamoDB, Secrets Manager)
2. Executa `terraform apply` para criar:
   - Bucket S3
   - Secrets Manager secret (com placeholder)
   - Tabelas DynamoDB
   - Lambda Function (dummy)
   - Step Functions
   - IAM Roles

### Configuração LocalStack

A configuração para LocalStack está em `override.tf`, que:
- Aponta todos os serviços AWS para `localhost:4566`
- Usa credenciais dummy (`test`/`test`)
- Desabilita validações de credenciais AWS

**Nota**: O arquivo `override.tf` não é commitado (`.gitignore`), pois é específico para desenvolvimento local.

## Variáveis de Ambiente

Configure as variáveis no arquivo `terraform.tfvars`:

```hcl
environment         = "dev"
s3_bucket_name      = "my-datalake-bucket"
credly_org_id       = "your-org-id"
secrets_manager_key = "credly/credentials"
```

## Notas Importantes

- O arquivo `terraform.tfvars` com valores de produção **NÃO deve** ser commitado
- Para produção, use Terraform Cloud ou variáveis de ambiente
- Certifique-se de ter as credenciais AWS configuradas
