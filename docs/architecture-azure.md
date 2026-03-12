# AICMMS — Azure Cloud Architecture

> **AI-native Computer Maintenance Management System**
> Prepared for: Project Management & Stakeholders
> Platform: Microsoft Azure

---

## 1. Solution Overview

```mermaid
graph TB
    subgraph USERS["👥 Users & Channels"]
        FM["Facility Managers<br/>Web Dashboard"]
        TECH["Technicians<br/>Mobile App"]
        MGMT["Management<br/>Reports & KPIs"]
        EXT["External Systems<br/>BMS · ERP · IoT"]
    end

    subgraph AZURE["☁️ Microsoft Azure Cloud"]

        subgraph FRONTEND["Presentation Tier"]
            CDN["Azure CDN<br/>Static Assets"]
            SWA["Azure Static Web Apps<br/>React Frontend"]
        end

        subgraph GATEWAY["API Gateway Tier"]
            APIM["Azure API Management<br/>Rate Limiting · Throttling<br/>API Versioning · Analytics"]
            AADB2C["Azure AD B2C<br/>Identity & Access<br/>SSO · MFA"]
        end

        subgraph APP["Application Tier"]
            ACA["Azure Container Apps<br/>FastAPI Backend<br/>Auto-scaling · Zero Downtime"]
            FUNC["Azure Functions<br/>Scheduled Jobs<br/>PPM · Reports · Sync"]
        end

        subgraph DATA["Data Tier"]
            SQLAZ["Azure SQL Database<br/>Core Business Data<br/>Assets · WOs · Facilities"]
            COSMOS["Azure Cosmos DB<br/>IoT Sensor Readings<br/>Audit Logs · Events"]
            BLOB["Azure Blob Storage<br/>Documents · Photos<br/>Voice Notes · Reports"]
            REDIS["Azure Cache for Redis<br/>Session · Rate Limiting<br/>Real-time Dashboard"]
        end

        subgraph AI_ML["AI & Intelligence Tier"]
            AOAI["Azure OpenAI Service<br/>GPT-4 · NLP Queries<br/>Document Generation"]
            COG["Azure AI Services<br/>Speech-to-Text<br/>Image Classification"]
            AISRCH["Azure AI Search<br/>Full-text · Vector Search<br/>Asset Knowledge Base"]
        end

        subgraph MESSAGING["Integration & Messaging"]
            SB["Azure Service Bus<br/>Event Queue<br/>Async Processing"]
            EG["Azure Event Grid<br/>Real-time Events<br/>IoT Alerts"]
            SGNLR["Azure SignalR Service<br/>WebSocket<br/>Live Dashboard"]
        end

        subgraph MONITOR["Operations & Monitoring"]
            APPINS["Application Insights<br/>APM · Traces · Metrics"]
            LOGAW["Log Analytics<br/>Centralized Logging"]
            ALERTS["Azure Monitor Alerts<br/>SLA Monitoring"]
        end

        subgraph SECURITY["Security & Compliance"]
            KV["Azure Key Vault<br/>Secrets · Certificates<br/>Connection Strings"]
            VNET["Azure Virtual Network<br/>Network Isolation"]
            WAF["Web Application Firewall<br/>DDoS Protection"]
        end

    end

    %% User connections
    FM --> CDN
    TECH --> CDN
    MGMT --> CDN
    FM --> SGNLR
    TECH --> SGNLR
    EXT --> APIM

    %% Frontend flow
    CDN --> SWA
    SWA --> APIM

    %% Gateway to App
    APIM --> AADB2C
    APIM --> ACA
    APIM --> WAF

    %% App to Data
    ACA --> SQLAZ
    ACA --> COSMOS
    ACA --> BLOB
    ACA --> REDIS
    ACA --> SB
    ACA --> SGNLR
    FUNC --> SQLAZ
    FUNC --> BLOB
    FUNC --> AOAI

    %% AI connections
    ACA --> AOAI
    ACA --> COG
    ACA --> AISRCH

    %% Messaging
    SB --> FUNC
    EG --> FUNC
    EG --> SGNLR

    %% Monitoring
    ACA --> APPINS
    FUNC --> APPINS
    APPINS --> LOGAW
    LOGAW --> ALERTS

    %% Security
    ACA --> KV
    FUNC --> KV
    ACA --> VNET

    classDef user fill:#4A90D9,stroke:#2C5F8A,color:#fff
    classDef frontend fill:#00B4D8,stroke:#0077B6,color:#fff
    classDef gateway fill:#E67E22,stroke:#D35400,color:#fff
    classDef app fill:#27AE60,stroke:#1E8449,color:#fff
    classDef data fill:#8E44AD,stroke:#6C3483,color:#fff
    classDef ai fill:#E74C3C,stroke:#C0392B,color:#fff
    classDef msg fill:#F39C12,stroke:#E67E22,color:#fff
    classDef monitor fill:#7F8C8D,stroke:#566573,color:#fff
    classDef security fill:#2C3E50,stroke:#1A252F,color:#fff

    class FM,TECH,MGMT,EXT user
    class CDN,SWA frontend
    class APIM,AADB2C gateway
    class ACA,FUNC app
    class SQLAZ,COSMOS,BLOB,REDIS data
    class AOAI,COG,AISRCH ai
    class SB,EG,SGNLR msg
    class APPINS,LOGAW,ALERTS monitor
    class KV,VNET,WAF security
```

---

## 2. Application Architecture — Layered View

```mermaid
graph TB
    subgraph L1["🌐 Presentation Layer"]
        direction LR
        WEB["React Web App<br/>Azure Static Web Apps"]
        MOBILE["Mobile App<br/>(Flutter / React Native)"]
        SWAGGER["API Docs<br/>Swagger / ReDoc"]
    end

    subgraph L2["🔐 API Gateway"]
        direction LR
        APIM["Azure API Management<br/>Versioning · Rate Limits · Analytics"]
        AUTH["Azure AD B2C<br/>JWT · RBAC · 5 Roles"]
    end

    subgraph L3["⚙️ Application Layer — FastAPI on Azure Container Apps"]
        direction TB

        subgraph ROUTES["16 API Endpoint Groups"]
            direction LR
            R1["Assets · Work Orders<br/>Technicians · Dashboard"]
            R2["Facilities · Maintenance<br/>Inspections · Vendors"]
            R3["Costs · Documents<br/>Sensors · Gamification"]
            R4["Query · Occupancy<br/>Connectors · Health"]
        end

        subgraph SVC["15 Service Modules"]
            direction LR
            SV1["AssetService<br/>WorkOrderService<br/>TechnicianService"]
            SV2["MaintenanceService<br/>InspectionService<br/>FacilityService"]
            SV3["CostService<br/>DocumentService<br/>VendorService"]
            SV4["SensorService<br/>GamificationService<br/>QueryService"]
        end

        subgraph DOMAIN["Domain Model — 13 Entity Groups · 50+ Models"]
            direction LR
            DM1["Assets · Work Orders<br/>Facilities · Maintenance"]
            DM2["Inspections · Technicians<br/>Vendors · Costs"]
            DM3["Documents · Sensors<br/>Gamification · Occupancy"]
        end
    end

    subgraph L4["💾 Data Access Layer"]
        direction LR
        REPO["Repository Pattern<br/>SQL · Mongo · File"]
        CONN["6 Connector Plugins<br/>PostgreSQL · MySQL · MSSQL<br/>MongoDB · CSV · Excel"]
        PIPE["ETL Pipeline Engine<br/>Extract → Transform → Load"]
    end

    subgraph L5["🗄️ Data & Storage Layer"]
        direction LR
        SQL["Azure SQL Database<br/>Relational Data"]
        COSM["Cosmos DB<br/>NoSQL / IoT"]
        BLOBS["Blob Storage<br/>Files & Media"]
        CACHE["Redis Cache<br/>Sessions"]
    end

    subgraph L6["🤖 AI & Intelligence"]
        direction LR
        GPT["Azure OpenAI (GPT-4)<br/>NLP Query · Document Gen"]
        SPEECH["Azure AI Speech<br/>Voice Note Transcription"]
        VISION["Azure AI Vision<br/>Photo Classification"]
        SEARCH["Azure AI Search<br/>Knowledge Base"]
    end

    L1 --> L2 --> L3
    ROUTES --> SVC --> DOMAIN
    L3 --> L4 --> L5
    L3 --> L6

    classDef l1Style fill:#00B4D8,stroke:#0077B6,color:#fff
    classDef l2Style fill:#E67E22,stroke:#D35400,color:#fff
    classDef l3Style fill:#27AE60,stroke:#1E8449,color:#fff
    classDef l4Style fill:#2980B9,stroke:#1F618D,color:#fff
    classDef l5Style fill:#8E44AD,stroke:#6C3483,color:#fff
    classDef l6Style fill:#E74C3C,stroke:#C0392B,color:#fff

    class WEB,MOBILE,SWAGGER l1Style
    class APIM,AUTH l2Style
    class R1,R2,R3,R4,SV1,SV2,SV3,SV4,DM1,DM2,DM3 l3Style
    class REPO,CONN,PIPE l4Style
    class SQL,COSM,BLOBS,CACHE l5Style
    class GPT,SPEECH,VISION,SEARCH l6Style
```

---

## 3. Azure Deployment Architecture

```mermaid
graph TB
    subgraph RG_PROD["Resource Group: rg-aicmms-prod"]

        subgraph NETWORK["Virtual Network: vnet-aicmms"]
            subgraph SUB_APP["Subnet: snet-app"]
                ACA1["Container App<br/>aicmms-api<br/>FastAPI Backend<br/>Min: 2 · Max: 10 replicas"]
            end
            subgraph SUB_DATA["Subnet: snet-data"]
                SQLAZ["Azure SQL<br/>sql-aicmms-prod<br/>General Purpose<br/>S2 (50 DTU)"]
                COSMOS["Cosmos DB<br/>cosmos-aicmms-prod<br/>Serverless<br/>1000 RU/s"]
            end
            subgraph SUB_CACHE["Subnet: snet-cache"]
                REDIS["Redis Cache<br/>redis-aicmms-prod<br/>Standard C1"]
            end
        end

        APIM["API Management<br/>apim-aicmms<br/>Developer Tier"]

        SWA["Static Web App<br/>swa-aicmms<br/>Standard Plan"]

        subgraph STORAGE["Storage"]
            BLOB["Storage Account<br/>staicmmsprod<br/>Hot: Documents, Photos<br/>Cool: Archives, Backups"]
        end

        subgraph FUNCTIONS["Serverless"]
            FUNC1["Function App<br/>func-aicmms-scheduler<br/>Consumption Plan"]
            FUNC2["Function App<br/>func-aicmms-reports<br/>Consumption Plan"]
        end

        subgraph AI_SERVICES["AI Services"]
            AOAI["OpenAI Service<br/>oai-aicmms<br/>GPT-4o · Ada Embeddings"]
            COGSVC["AI Services (Multi)<br/>cog-aicmms<br/>Speech · Vision"]
            AISEARCH["AI Search<br/>srch-aicmms<br/>Basic Tier"]
        end

        subgraph MESSAGING_SVC["Messaging"]
            SBUS["Service Bus<br/>sb-aicmms<br/>Standard Tier"]
            SIGNALR["SignalR Service<br/>signalr-aicmms<br/>Free → Standard"]
            EVGRID["Event Grid<br/>System Topics"]
        end

        subgraph OPS["Operations"]
            APPINS["App Insights<br/>appi-aicmms"]
            LOGWS["Log Analytics<br/>log-aicmms"]
            KV["Key Vault<br/>kv-aicmms"]
        end

    end

    subgraph RG_DEV["Resource Group: rg-aicmms-dev"]
        DEV_ACA["Container App (Dev)"]
        DEV_SQL["Azure SQL (Dev)<br/>Basic Tier"]
        DEV_BLOB["Storage (Dev)"]
    end

    subgraph RG_STAGING["Resource Group: rg-aicmms-staging"]
        STG_ACA["Container App (Staging)"]
        STG_SQL["Azure SQL (Staging)<br/>S1 Tier"]
        STG_BLOB["Storage (Staging)"]
    end

    %% Network flow
    APIM --> ACA1
    SWA --> APIM
    ACA1 --> SQLAZ
    ACA1 --> COSMOS
    ACA1 --> REDIS
    ACA1 --> BLOB
    ACA1 --> SBUS
    ACA1 --> SIGNALR
    ACA1 --> AOAI
    ACA1 --> COGSVC
    ACA1 --> KV
    ACA1 --> APPINS
    SBUS --> FUNC1
    FUNC1 --> SQLAZ
    FUNC2 --> BLOB
    FUNC2 --> AOAI

    classDef compute fill:#27AE60,stroke:#1E8449,color:#fff
    classDef data fill:#8E44AD,stroke:#6C3483,color:#fff
    classDef ai fill:#E74C3C,stroke:#C0392B,color:#fff
    classDef msg fill:#F39C12,stroke:#E67E22,color:#fff
    classDef ops fill:#7F8C8D,stroke:#566573,color:#fff
    classDef dev fill:#95A5A6,stroke:#7F8C8D,color:#fff

    class ACA1,FUNC1,FUNC2,SWA,APIM compute
    class SQLAZ,COSMOS,REDIS,BLOB data
    class AOAI,COGSVC,AISEARCH ai
    class SBUS,SIGNALR,EVGRID msg
    class APPINS,LOGWS,KV ops
    class DEV_ACA,DEV_SQL,DEV_BLOB,STG_ACA,STG_SQL,STG_BLOB dev
```

---

## 4. CI/CD Pipeline — Azure DevOps

```mermaid
graph LR
    subgraph DEV["Developer Workflow"]
        CODE["Code Push<br/>GitHub / Azure Repos"]
        PR["Pull Request<br/>Code Review"]
    end

    subgraph CI["Continuous Integration"]
        BUILD["Build & Test<br/>Python 3.12<br/>162 Unit Tests"]
        LINT["Linting & Security<br/>Ruff · Bandit · Safety"]
        DOCKER["Docker Build<br/>Multi-stage Image<br/>~150MB Final"]
        ACR["Push to ACR<br/>Azure Container Registry"]
    end

    subgraph CD_DEV["Deploy → Dev"]
        DEV_DEPLOY["Container Apps (Dev)<br/>Auto-deploy on merge"]
        DEV_TEST["Integration Tests<br/>API Smoke Tests"]
    end

    subgraph CD_STG["Deploy → Staging"]
        STG_DEPLOY["Container Apps (Staging)<br/>Manual Approval Gate"]
        STG_TEST["E2E Tests<br/>Load Tests"]
    end

    subgraph CD_PROD["Deploy → Production"]
        PROD_APPROVE["PM Approval Gate<br/>Change Advisory Board"]
        PROD_DEPLOY["Container Apps (Prod)<br/>Blue-Green Deployment<br/>Zero Downtime"]
        PROD_VERIFY["Health Check<br/>Canary Validation"]
    end

    CODE --> PR --> BUILD --> LINT --> DOCKER --> ACR
    ACR --> DEV_DEPLOY --> DEV_TEST
    DEV_TEST --> STG_DEPLOY --> STG_TEST
    STG_TEST --> PROD_APPROVE --> PROD_DEPLOY --> PROD_VERIFY

    classDef devStyle fill:#4A90D9,stroke:#2C5F8A,color:#fff
    classDef ciStyle fill:#E67E22,stroke:#D35400,color:#fff
    classDef cdDev fill:#27AE60,stroke:#1E8449,color:#fff
    classDef cdStg fill:#F39C12,stroke:#E67E22,color:#fff
    classDef cdProd fill:#E74C3C,stroke:#C0392B,color:#fff

    class CODE,PR devStyle
    class BUILD,LINT,DOCKER,ACR ciStyle
    class DEV_DEPLOY,DEV_TEST cdDev
    class STG_DEPLOY,STG_TEST cdStg
    class PROD_APPROVE,PROD_DEPLOY,PROD_VERIFY cdProd
```

---

## 5. Data Flow Architecture

```mermaid
graph TB
    subgraph INGEST["Data Ingestion"]
        BMS["BMS Systems<br/>Building Sensors"]
        ERP["ERP Integration<br/>SAP / Oracle"]
        IOT["IoT Devices<br/>Temperature · Humidity<br/>Energy · Occupancy"]
        EXCEL["Excel Imports<br/>Asset Registers<br/>Vendor Lists"]
        MOBILE_IN["Mobile Input<br/>Voice Notes · Photos<br/>QR Scans"]
    end

    subgraph PROCESS["Processing Layer (Azure Container Apps)"]
        CONN_FW["Connector Framework<br/>6 Plugin Types<br/>Auto-discovery"]
        ETL["ETL Pipeline<br/>Extract → Transform → Load<br/>Schema Mapping"]
        AI_PROC["AI Processing<br/>NLP Classification<br/>Anomaly Detection<br/>Predictive Maintenance"]
        EVENT["Event Bus<br/>Real-time Processing<br/>Threshold Alerts"]
    end

    subgraph STORE["Storage Layer"]
        direction LR
        subgraph OPERATIONAL["Operational Data"]
            SQL_OP["Azure SQL<br/>Assets · Work Orders<br/>Vendors · Schedules<br/>Users · Permissions"]
        end
        subgraph ANALYTICAL["Analytical Data"]
            COSMOS_AN["Cosmos DB<br/>Sensor Readings<br/>Audit Trail<br/>Query History"]
        end
        subgraph MEDIA["Media & Documents"]
            BLOB_M["Blob Storage<br/>Inspection Photos<br/>Voice Recordings<br/>Generated Reports<br/>Excel Templates"]
        end
        subgraph INTELLIGENCE["Intelligence"]
            SEARCH_I["AI Search Index<br/>Asset Knowledge<br/>Full-text Search<br/>Vector Embeddings"]
        end
    end

    subgraph OUTPUT["Output Channels"]
        DASH["Real-time Dashboard<br/>KPIs · Alerts · Heatmaps"]
        REPORTS["Automated Reports<br/>Daily · Weekly · Monthly"]
        NOTIF["Notifications<br/>Email · Push · SMS"]
        API_OUT["API Responses<br/>REST · WebSocket"]
    end

    %% Ingestion to Processing
    BMS --> CONN_FW
    ERP --> CONN_FW
    IOT --> EVENT
    EXCEL --> ETL
    MOBILE_IN --> AI_PROC

    %% Processing to Storage
    CONN_FW --> ETL --> SQL_OP
    EVENT --> COSMOS_AN
    AI_PROC --> SEARCH_I
    MOBILE_IN --> BLOB_M

    %% Storage to Output
    SQL_OP --> DASH
    SQL_OP --> REPORTS
    COSMOS_AN --> DASH
    SEARCH_I --> API_OUT
    EVENT --> NOTIF
    EVENT --> DASH

    classDef ingest fill:#4A90D9,stroke:#2C5F8A,color:#fff
    classDef process fill:#27AE60,stroke:#1E8449,color:#fff
    classDef store fill:#8E44AD,stroke:#6C3483,color:#fff
    classDef output fill:#E67E22,stroke:#D35400,color:#fff

    class BMS,ERP,IOT,EXCEL,MOBILE_IN ingest
    class CONN_FW,ETL,AI_PROC,EVENT process
    class SQL_OP,COSMOS_AN,BLOB_M,SEARCH_I store
    class DASH,REPORTS,NOTIF,API_OUT output
```

---

## 6. Security Architecture

```mermaid
graph TB
    subgraph PERIMETER["Network Perimeter"]
        WAF["Azure WAF<br/>DDoS Protection<br/>OWASP Rules"]
        FD["Azure Front Door<br/>Global Load Balancing<br/>SSL Termination"]
    end

    subgraph IDENTITY["Identity & Access"]
        B2C["Azure AD B2C<br/>User Authentication<br/>SSO · MFA"]
        RBAC_AZ["Azure RBAC<br/>Resource Permissions"]
        subgraph APP_ROLES["Application Roles"]
            ADMIN["Admin<br/>Full System Access"]
            MANAGER["Manager<br/>Read/Write + Approvals"]
            TECHNICIAN["Technician<br/>Field Operations"]
            VIEWER["Viewer<br/>Read-Only Access"]
            SYSTEM["System<br/>Internal Services"]
        end
    end

    subgraph DATA_SEC["Data Security"]
        KV_S["Key Vault<br/>Secrets Management<br/>Connection Strings<br/>API Keys"]
        TDE["Transparent Data Encryption<br/>Azure SQL · Cosmos DB"]
        BLOB_ENC["Blob Encryption<br/>AES-256 at Rest"]
        TLS["TLS 1.3<br/>In Transit"]
    end

    subgraph COMPLIANCE["Compliance & Audit"]
        AUDIT["Audit Logging<br/>All API Operations"]
        DIAG["Diagnostic Settings<br/>Activity Logs"]
        POLICY["Azure Policy<br/>Governance Rules"]
    end

    FD --> WAF --> B2C
    B2C --> APP_ROLES
    APP_ROLES --> KV_S
    KV_S --> TDE
    KV_S --> BLOB_ENC
    AUDIT --> DIAG --> POLICY

    classDef perimeter fill:#E74C3C,stroke:#C0392B,color:#fff
    classDef identity fill:#E67E22,stroke:#D35400,color:#fff
    classDef role fill:#8E44AD,stroke:#6C3483,color:#fff
    classDef datasec fill:#2980B9,stroke:#1F618D,color:#fff
    classDef comply fill:#7F8C8D,stroke:#566573,color:#fff

    class WAF,FD perimeter
    class B2C,RBAC_AZ identity
    class ADMIN,MANAGER,TECHNICIAN,VIEWER,SYSTEM role
    class KV_S,TDE,BLOB_ENC,TLS datasec
    class AUDIT,DIAG,POLICY comply
```

---

## 7. MVP User Stories → Azure Services Mapping

| # | User Story | Application Layer | Azure Services |
|---|-----------|-------------------|----------------|
| 1 | **Data Source Connectors** | ConnectorService + 6 Plugins | Azure SQL · Cosmos DB · Blob Storage |
| 2 | **FM Command Center** | DashboardService + FacilityService | SignalR (live) · Redis (cache) · App Insights |
| 3 | **PPM Scheduling** | MaintenanceService | Azure Functions (scheduler) · Service Bus |
| 4 | **NLP Query Interface** | QueryService | Azure OpenAI GPT-4o · AI Search |
| 5 | **Ad-hoc Work Orders** | WorkOrderService | Azure SQL · Service Bus (notifications) |
| 6 | **Excel-native UI** | DocumentService | Blob Storage · Azure SQL |
| 7 | **Excel Import** | DocumentService + ETL Pipeline | Blob Storage · Azure Functions |
| 8 | **Native Asset Onboarding** | AssetService (QR Gen) | Azure SQL · Blob Storage |
| 9 | **Document Templates** | DocumentService | Azure OpenAI (generation) · Blob Storage |
| 10 | **FM Reporting** | DocumentService + Scheduler | Azure Functions (cron) · Blob Storage |
| 11 | **Sub-Vendor Management** | VendorService | Azure SQL · Service Bus |
| 12 | **WO → Commercial Journey** | CostService | Azure SQL · App Insights (tracking) |
| 13 | **Manpower Registry** | TechnicianService | Azure SQL · AI Search (skill matching) |
| 14 | **Inspection Reports** | InspectionService | AI Speech (voice) · AI Vision (photos) · Blob |
| 15 | **Gamified Self-Entry** | GamificationService | Azure SQL · SignalR (leaderboard) |
| 16 | **QR Scan Insights** | InspectionService | Azure OpenAI (classify) · Cosmos DB |

---

## 8. Azure Cost Estimation (Monthly)

### MVP Phase — Development & Testing

| Azure Service | SKU / Tier | Est. Monthly Cost |
|--------------|-----------|-------------------|
| Container Apps | Consumption (2 replicas) | ~$50–100 |
| Azure SQL Database | Basic (5 DTU) | ~$5 |
| Cosmos DB | Serverless (400 RU/s) | ~$25 |
| Blob Storage | Hot (50 GB) | ~$2 |
| Redis Cache | Basic C0 | ~$16 |
| Azure OpenAI | Pay-per-use (GPT-4o) | ~$30–60 |
| AI Services | Pay-per-use | ~$10–20 |
| AI Search | Free Tier | $0 |
| Service Bus | Basic | ~$0.05 |
| SignalR | Free (20 connections) | $0 |
| API Management | Consumption | ~$3.50/million calls |
| Static Web Apps | Free | $0 |
| Key Vault | Standard | ~$0.03/operation |
| App Insights | First 5 GB free | $0 |
| **Total MVP/Dev** | | **~$150–250/month** |

### Production Phase — Full Scale

| Azure Service | SKU / Tier | Est. Monthly Cost |
|--------------|-----------|-------------------|
| Container Apps | Dedicated (2–10 replicas) | ~$200–500 |
| Azure SQL Database | S2 General Purpose (50 DTU) | ~$75 |
| Cosmos DB | Provisioned (1000 RU/s) | ~$60 |
| Blob Storage | Hot (500 GB) + Cool (1 TB) | ~$25 |
| Redis Cache | Standard C1 | ~$80 |
| Azure OpenAI | GPT-4o (moderate usage) | ~$100–300 |
| AI Services | Speech + Vision | ~$50–100 |
| AI Search | Basic (15 GB index) | ~$75 |
| Service Bus | Standard | ~$10 |
| SignalR | Standard (1000 connections) | ~$50 |
| API Management | Developer | ~$50 |
| Static Web Apps | Standard | ~$9 |
| Azure Front Door | Standard | ~$35 |
| Key Vault | Standard | ~$5 |
| App Insights | 10 GB/month | ~$25 |
| **Total Production** | | **~$850–1,400/month** |

> **Note:** Costs are estimates based on Azure pricing as of 2026. Actual costs depend on usage patterns, data volume, and API call frequency.

---

## 9. Environment Strategy

```mermaid
graph LR
    subgraph ENVS["Three Environment Strategy"]
        DEV["🔧 Development<br/>rg-aicmms-dev<br/><br/>• Minimal SKUs<br/>• Shared DB<br/>• Mock AI Services<br/>• Auto-deploy on PR merge"]
        STG["🧪 Staging<br/>rg-aicmms-staging<br/><br/>• Production-like SKUs<br/>• Anonymized data copy<br/>• Real AI Services<br/>• Manual promotion"]
        PROD["🚀 Production<br/>rg-aicmms-prod<br/><br/>• Full-scale SKUs<br/>• HA + Auto-scaling<br/>• Geo-redundant backups<br/>• Blue-Green deployment"]
    end

    DEV -->|"Automated<br/>Tests Pass"| STG
    STG -->|"PM Approval<br/>+ UAT Sign-off"| PROD

    classDef devEnv fill:#27AE60,stroke:#1E8449,color:#fff
    classDef stgEnv fill:#F39C12,stroke:#E67E22,color:#fff
    classDef prodEnv fill:#E74C3C,stroke:#C0392B,color:#fff

    class DEV devEnv
    class STG stgEnv
    class PROD prodEnv
```

---

## 10. Project Metrics (Current Status)

| Metric | Value |
|--------|-------|
| **Total Source Files** | 100+ |
| **Lines of Code** | 12,000+ |
| **API Endpoints** | 16 route groups, 80+ endpoints |
| **Service Modules** | 15 |
| **Domain Models** | 50+ (13 entity groups) |
| **Connector Plugins** | 6 (PostgreSQL, MySQL, MSSQL, MongoDB, CSV, Excel) |
| **Unit Tests** | 162 passing |
| **Test Coverage** | Core services, schemas, middleware, WebSocket |
| **MVP Stories Covered** | 16/16 (API layer complete) |
| **Git Commits** | 6 on master |

### Build Status

| Component | Status |
|-----------|--------|
| Core Platform | ✅ Complete |
| Connector Framework | ✅ Complete (6 plugins) |
| Schema Discovery | ✅ Complete |
| Domain Models | ✅ Complete (50+ models) |
| Repository Layer | ✅ Complete |
| Integration Engine | ✅ Complete (ETL + Scheduler) |
| AI Foundation | ✅ Complete (interfaces + embeddings) |
| API Layer | ✅ Complete (all 16 stories) |
| Service Layer | ✅ Complete (15 services) |
| Unit Tests | ✅ 162 passing |
| Frontend | 🔲 Not started |
| Azure Deployment | 🔲 Not started |
| E2E Tests | 🔲 Not started |

---

## 11. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Backend Framework** | FastAPI (Python) | Async-native, auto-docs, Pydantic validation, fast development |
| **Cloud Platform** | Microsoft Azure | Enterprise-grade, AI services, compliance certifications |
| **Container Orchestration** | Azure Container Apps | Serverless containers, auto-scaling, simpler than AKS |
| **Primary Database** | Azure SQL | Relational integrity for core business data, familiar tooling |
| **NoSQL / IoT Store** | Cosmos DB | Serverless scaling for high-volume sensor data |
| **Real-time Updates** | Azure SignalR | Managed WebSocket, scales to thousands of connections |
| **AI/NLP Engine** | Azure OpenAI (GPT-4o) | Best-in-class NLP, native Azure integration |
| **Authentication** | Azure AD B2C | Enterprise SSO, MFA, social login, RBAC |
| **Job Scheduling** | Azure Functions | Consumption pricing, event-driven, timer triggers |
| **API Gateway** | Azure API Management | Rate limiting, versioning, analytics, developer portal |
| **Secrets Management** | Azure Key Vault | HSM-backed, access policies, rotation support |

---

## 12. Non-Functional Requirements

| Requirement | Target | Azure Service |
|------------|--------|---------------|
| **Availability** | 99.9% SLA | Container Apps + Azure SQL (zone redundant) |
| **Response Time** | < 200ms (p95) | Redis Cache + Container Apps auto-scale |
| **Concurrent Users** | 500+ simultaneous | SignalR Standard + Container Apps (10 replicas) |
| **Data Retention** | 7 years | Blob Storage (Cool/Archive tier) |
| **Backup RPO** | 1 hour | Azure SQL point-in-time restore |
| **Backup RTO** | 4 hours | Geo-redundant backups |
| **Security** | SOC 2, ISO 27001 | Azure compliance certifications |
| **Scalability** | Auto-scale 2–10 instances | Container Apps scaling rules |
| **Monitoring** | Real-time APM | Application Insights + Log Analytics |
