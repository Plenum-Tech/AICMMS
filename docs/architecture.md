# AICMMS Architecture

## High-Level System Architecture

```mermaid
graph TB
    subgraph Clients["Clients"]
        WEB["Web Frontend<br/>(React/Next.js)"]
        MOB["Mobile App<br/>(Flutter/RN)"]
        EXT["External Systems<br/>(BMS, ERP)"]
    end

    subgraph API_LAYER["API Gateway — FastAPI"]
        direction TB
        MW["Middleware Stack<br/>CORS · Rate Limit · Logging"]
        AUTH["Auth & RBAC<br/>JWT · 5 Roles · Permission Matrix"]
        WS["WebSocket<br/>/ws/dashboard"]
        REST["REST API v1<br/>/api/v1/*"]
    end

    subgraph ROUTES["API Routes — 16 Endpoint Groups"]
        R_ASSET["Assets<br/>CRUD · QR · Stats"]
        R_WO["Work Orders<br/>CRUD · Ad-hoc · Transitions"]
        R_MAINT["Maintenance<br/>PPM · Insights · Logs"]
        R_FACIL["Facilities<br/>Buildings · Floors · Spaces"]
        R_INSP["Inspections<br/>Voice · Photos · AI Classify"]
        R_TECH["Technicians<br/>Skills · Routing · Gamification"]
        R_VEND["Vendors<br/>Contracts · SLAs · Performance"]
        R_COST["Costs<br/>Expenses · Invoices · Budgets"]
        R_DOC["Documents<br/>Templates · Reports · Excel"]
        R_SENS["Sensors<br/>IoT Devices · Readings"]
        R_GAM["Gamification<br/>Profiles · Leaderboard · Badges"]
        R_QUERY["Query Interface<br/>NLP · Voice · Multi-modal"]
        R_OCC["Occupancy<br/>Utilization · Heatmaps"]
        R_DASH["Dashboard<br/>KPIs · Alerts · Breakdown"]
        R_CONN["Connectors<br/>Register · Schema · Query"]
        R_HEALTH["Health<br/>Liveness · Readiness"]
    end

    subgraph SERVICES["Service Layer — Business Logic"]
        S1["AssetService"]
        S2["WorkOrderService"]
        S3["MaintenanceService"]
        S4["FacilityService"]
        S5["InspectionService"]
        S6["TechnicianService"]
        S7["VendorService"]
        S8["CostService"]
        S9["DocumentService"]
        S10["SensorService"]
        S11["GamificationService"]
        S12["QueryService"]
        S13["OccupancyService"]
        S14["DashboardService"]
        S15["ConnectorService"]
    end

    subgraph DOMAIN["Domain Models — 13 Entity Groups"]
        D_ASSET["Asset · AssetCategory<br/>AssetLifecycleEvent"]
        D_WO["WorkOrder<br/>WorkOrderTask"]
        D_MAINT["MaintenanceSchedule<br/>MaintenanceLog · FailureMode"]
        D_FACIL["Building · Floor<br/>Space · Zone"]
        D_INSP["InspectionReport<br/>InspectionFinding · Template"]
        D_TECH["Technician<br/>TechnicianSkill · Availability"]
        D_VEND["Vendor · Contract<br/>ServiceLevel"]
        D_COST["Expense · Invoice<br/>Budget · CostCenter"]
        D_DOC["DocumentTemplate<br/>GeneratedDocument · ReportSchedule"]
        D_SENS["IoTDevice · SensorReading<br/>Threshold"]
        D_GAM["GamificationProfile<br/>Badge · PointTransaction · AssetInsight"]
        D_OCC["OccupancyData · SpaceUtilization<br/>Reservation · MoveRequest"]
        D_ENUM["Enums<br/>AssetStatus · WOStatus · VendorType<br/>+ 15 more"]
    end

    subgraph REPOSITORY["Repository Layer — Data Abstraction"]
        REPO_BASE["Repository&lt;T&gt; Interface"]
        REPO_SQL["SQLRepository"]
        REPO_MONGO["MongoRepository"]
        REPO_FILE["FileRepository"]
        UOW["UnitOfWork<br/>Transaction Pattern"]
    end

    subgraph INTEGRATION["Integration & Pipeline Engine"]
        IM["IntegrationManager<br/>(Central Orchestrator)"]
        PIPE["Pipeline<br/>Extract → Transform → Load"]
        SCHED["Scheduler<br/>Cron-like Job Runner"]
        SYNC["DataSync<br/>Incremental · Full"]
        XFORM["Transforms<br/>Rename · Cast · Filter · Dedup"]
    end

    subgraph CONNECTORS["Connector Plugin Framework"]
        CR["ConnectorRegistry<br/>Auto-discovery via entry_points"]
        LM["LifecycleManager<br/>Health Checks · Reconnect"]
        CF["ConnectorFactory"]
        subgraph PLUGINS["Plugins"]
            PG["PostgreSQL<br/>SQLAlchemy Async"]
            MY["MySQL<br/>SQLAlchemy Async"]
            MS["MS SQL Server<br/>SQLAlchemy Async"]
            MO["MongoDB<br/>Motor Async"]
            CSV_P["CSV<br/>Pandas"]
            XLS["Excel<br/>Pandas"]
        end
    end

    subgraph SCHEMA_LAYER["Schema Discovery"]
        SD["SchemaDiscoveryService"]
        SM["DataSourceSchema<br/>TableSchema · ColumnSchema"]
        DIFF["SchemaDiff<br/>Change Detection"]
    end

    subgraph AI_LAYER["AI Foundation"]
        AI_IF["Data Provider Interfaces"]
        AI_CTX["LLM Context Builder"]
        AI_DS["DatasetBuilder"]
        AI_EMB["EmbeddingStore<br/>Vector Search"]
        AI_FS["FeatureStore"]
    end

    subgraph CORE["Core Infrastructure"]
        EB["EventBus<br/>Pub/Sub · Async"]
        CFG["AppConfig · APIConfig<br/>Environment-based"]
        EXC["Exception Hierarchy<br/>CAFMError → 7 subtypes"]
        TYPES["Unified Type System<br/>DataSourceType · UnifiedDataType"]
        LOG["Structured Logging"]
        BASE["CAFMBaseModel<br/>Audit · Soft-delete"]
    end

    %% Client connections
    WEB --> REST
    WEB --> WS
    MOB --> REST
    MOB --> WS
    EXT --> REST

    %% API flow
    REST --> MW --> AUTH --> ROUTES
    WS --> MW

    %% Routes to Services
    ROUTES --> SERVICES

    %% Services use Domain + Repository + Events
    SERVICES --> DOMAIN
    SERVICES --> REPO_BASE
    SERVICES --> EB

    %% Repository implementations
    REPO_BASE --> REPO_SQL
    REPO_BASE --> REPO_MONGO
    REPO_BASE --> REPO_FILE

    %% Repository → Connector
    REPO_SQL --> PG
    REPO_SQL --> MY
    REPO_SQL --> MS
    REPO_MONGO --> MO
    REPO_FILE --> CSV_P
    REPO_FILE --> XLS

    %% Integration flow
    IM --> CR
    IM --> LM
    IM --> SD
    IM --> PIPE
    IM --> SCHED
    PIPE --> XFORM

    %% Connector framework
    CR --> CF --> PLUGINS
    LM --> PLUGINS

    %% Schema discovery
    SD --> PLUGINS
    SD --> SM

    %% AI uses domain + events
    AI_IF --> DOMAIN
    AI_CTX --> AI_IF
    AI_DS --> AI_IF
    AI_EMB --> CORE

    %% WebSocket bridge
    EB --> WS

    %% Core used everywhere
    CORE -.-> SERVICES
    CORE -.-> CONNECTORS
    CORE -.-> INTEGRATION

    %% Styling
    classDef clientStyle fill:#4A90D9,stroke:#2C5F8A,color:#fff
    classDef apiStyle fill:#E67E22,stroke:#D35400,color:#fff
    classDef routeStyle fill:#F39C12,stroke:#E67E22,color:#fff
    classDef serviceStyle fill:#27AE60,stroke:#1E8449,color:#fff
    classDef domainStyle fill:#8E44AD,stroke:#6C3483,color:#fff
    classDef repoStyle fill:#2980B9,stroke:#1F618D,color:#fff
    classDef connStyle fill:#16A085,stroke:#117A65,color:#fff
    classDef coreStyle fill:#7F8C8D,stroke:#566573,color:#fff
    classDef aiStyle fill:#E74C3C,stroke:#C0392B,color:#fff

    class WEB,MOB,EXT clientStyle
    class MW,AUTH,WS,REST apiStyle
    class R_ASSET,R_WO,R_MAINT,R_FACIL,R_INSP,R_TECH,R_VEND,R_COST,R_DOC,R_SENS,R_GAM,R_QUERY,R_OCC,R_DASH,R_CONN,R_HEALTH routeStyle
    class S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12,S13,S14,S15 serviceStyle
    class D_ASSET,D_WO,D_MAINT,D_FACIL,D_INSP,D_TECH,D_VEND,D_COST,D_DOC,D_SENS,D_GAM,D_OCC,D_ENUM domainStyle
    class REPO_BASE,REPO_SQL,REPO_MONGO,REPO_FILE,UOW repoStyle
    class CR,LM,CF,PG,MY,MS,MO,CSV_P,XLS connStyle
    class EB,CFG,EXC,TYPES,LOG,BASE coreStyle
    class AI_IF,AI_CTX,AI_DS,AI_EMB,AI_FS aiStyle
    class IM,PIPE,SCHED,SYNC,XFORM connStyle
    class SD,SM,DIFF repoStyle
```

## Layered Architecture (Simplified)

```mermaid
graph LR
    subgraph L1["Layer 1: Presentation"]
        API["FastAPI<br/>16 Route Groups<br/>JWT Auth · RBAC<br/>WebSocket"]
    end

    subgraph L2["Layer 2: Business Logic"]
        SVC["15 Services<br/>Domain Rules<br/>Event Publishing<br/>AI Integration"]
    end

    subgraph L3["Layer 3: Domain"]
        DOM["13 Entity Groups<br/>50+ Models<br/>Pydantic v2<br/>Audit Trail"]
    end

    subgraph L4["Layer 4: Data Access"]
        REPO["Repository Pattern<br/>SQL · Mongo · File<br/>Unit of Work"]
    end

    subgraph L5["Layer 5: Integration"]
        INT["Connector Plugins<br/>ETL Pipelines<br/>Schema Discovery<br/>Job Scheduler"]
    end

    subgraph L6["Layer 6: Data Sources"]
        DS["PostgreSQL · MySQL · MSSQL<br/>MongoDB · CSV · Excel<br/>BMS · ERP · IoT"]
    end

    API --> SVC --> DOM
    SVC --> REPO --> INT --> DS

    classDef l1 fill:#E67E22,stroke:#D35400,color:#fff
    classDef l2 fill:#27AE60,stroke:#1E8449,color:#fff
    classDef l3 fill:#8E44AD,stroke:#6C3483,color:#fff
    classDef l4 fill:#2980B9,stroke:#1F618D,color:#fff
    classDef l5 fill:#16A085,stroke:#117A65,color:#fff
    classDef l6 fill:#7F8C8D,stroke:#566573,color:#fff

    class API l1
    class SVC l2
    class DOM l3
    class REPO l4
    class INT l5
    class DS l6
```

## Data Flow — API Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as Middleware
    participant AUTH as Auth
    participant R as Route
    participant S as Service
    participant REPO as Repository
    participant CONN as Connector
    participant DB as Data Source
    participant EB as EventBus
    participant WS as WebSocket

    C->>MW: HTTP Request
    MW->>MW: Rate Limit Check
    MW->>MW: Request Logging
    MW->>AUTH: Extract JWT
    AUTH->>AUTH: Decode Token
    AUTH->>AUTH: Check RBAC Permission
    AUTH->>R: UserInfo + Request
    R->>R: Validate Schema (Pydantic)
    R->>S: Call Service Method
    S->>REPO: Repository Query
    REPO->>CONN: Connector Operation
    CONN->>DB: Database Query
    DB-->>CONN: Raw Rows
    CONN-->>REPO: RawRow List
    REPO-->>S: UnifiedResultSet
    S->>S: Business Logic
    S->>EB: Publish Event
    EB-->>WS: Bridge to WebSocket
    WS-->>C: Real-time Update
    S-->>R: Domain Entity
    R-->>C: APIResponse JSON
```

## Connector Plugin Architecture

```mermaid
graph TB
    subgraph REGISTRY["ConnectorRegistry (Singleton)"]
        EP["entry_points Discovery<br/>cafm.connectors group"]
        MAP["Plugin Map<br/>DataSourceType → Connector Class"]
    end

    subgraph LIFECYCLE["LifecycleManager"]
        HC["Health Checks<br/>Periodic Ping"]
        RC["Auto-Reconnect<br/>Exponential Backoff"]
        GS["Graceful Shutdown<br/>Connection Drain"]
    end

    subgraph FACTORY["ConnectorFactory"]
        CF["create_connector(config)<br/>→ Typed Connector Instance"]
    end

    subgraph ABC["Abstract Base"]
        CONN_IF["Connector Interface"]
        SI_IF["SchemaInspector Interface"]
    end

    subgraph IMPLS["Plugin Implementations"]
        PG["PostgreSQL Plugin<br/>SQLAlchemy Async<br/>pg_catalog inspection"]
        MY["MySQL Plugin<br/>SQLAlchemy Async<br/>INFORMATION_SCHEMA"]
        MS["MSSQL Plugin<br/>SQLAlchemy Async<br/>sys.tables inspection"]
        MO["MongoDB Plugin<br/>Motor Async<br/>Collection sampling"]
        CSV_I["CSV Plugin<br/>Pandas read_csv<br/>Type inference"]
        XLS_I["Excel Plugin<br/>Pandas read_excel<br/>Sheet discovery"]
    end

    EP --> MAP
    MAP --> FACTORY
    FACTORY --> IMPLS
    LIFECYCLE --> IMPLS
    CONN_IF --> IMPLS
    SI_IF --> IMPLS

    CONN_IF -.- |connect / disconnect / health_check| CONN_IF
    CONN_IF -.- |fetch_rows / insert_rows / execute_raw| CONN_IF
    SI_IF -.- |list_tables / discover_table / discover_schema| SI_IF

    classDef registry fill:#16A085,stroke:#117A65,color:#fff
    classDef lifecycle fill:#2980B9,stroke:#1F618D,color:#fff
    classDef abc fill:#8E44AD,stroke:#6C3483,color:#fff
    classDef impl fill:#27AE60,stroke:#1E8449,color:#fff

    class EP,MAP registry
    class HC,RC,GS lifecycle
    class CF lifecycle
    class CONN_IF,SI_IF abc
    class PG,MY,MS,MO,CSV_I,XLS_I impl
```

## Event-Driven Architecture

```mermaid
graph LR
    subgraph PUBLISHERS["Event Publishers"]
        P1["Services<br/>RECORD_CREATED<br/>RECORD_UPDATED<br/>RECORD_DELETED"]
        P2["Connectors<br/>CONNECTOR_REGISTERED<br/>CONNECTOR_CONNECTED<br/>CONNECTOR_ERROR"]
        P3["Pipelines<br/>PIPELINE_STARTED<br/>PIPELINE_COMPLETED<br/>PIPELINE_FAILED"]
        P4["Sensors<br/>THRESHOLD_BREACHED<br/>ANOMALY_DETECTED"]
        P5["Schema<br/>SCHEMA_DISCOVERED<br/>SCHEMA_CHANGED"]
    end

    EB["EventBus<br/>(In-Process Pub/Sub)<br/>Async + Sync Support"]

    subgraph SUBSCRIBERS["Event Subscribers"]
        S1["WebSocket Bridge<br/>→ Real-time Dashboard"]
        S2["Notification Service<br/>→ Alerts & Emails"]
        S3["Audit Logger<br/>→ Change Tracking"]
        S4["AI Engine<br/>→ Model Re-training"]
        S5["Pipeline Trigger<br/>→ Data Sync"]
    end

    P1 --> EB
    P2 --> EB
    P3 --> EB
    P4 --> EB
    P5 --> EB

    EB --> S1
    EB --> S2
    EB --> S3
    EB --> S4
    EB --> S5

    classDef pub fill:#E67E22,stroke:#D35400,color:#fff
    classDef bus fill:#E74C3C,stroke:#C0392B,color:#fff
    classDef sub fill:#27AE60,stroke:#1E8449,color:#fff

    class P1,P2,P3,P4,P5 pub
    class EB bus
    class S1,S2,S3,S4,S5 sub
```

## Authentication & Authorization Flow

```mermaid
graph TB
    subgraph ROLES["5 User Roles"]
        ADMIN["Admin<br/>Full Access"]
        MGR["Manager<br/>Read/Write + Approve"]
        TECH["Technician<br/>Own Records + Execute"]
        VIEW["Viewer<br/>Read-Only"]
        SYS["System<br/>Internal Operations"]
    end

    subgraph AUTH_FLOW["Authentication Flow"]
        LOGIN["POST /auth/token<br/>Username + Password"]
        JWT["JWT Token<br/>jose · HS256<br/>Configurable Expiry"]
        DECODE["Token Decode<br/>→ UserInfo + Role"]
    end

    subgraph RBAC["RBAC Permission Matrix"]
        PERM["Permission Check<br/>require_permission()"]
        DEP["Dependency Injection<br/>get_current_user()"]
    end

    subgraph PERMS["Permission Sets"]
        P_R["*:read<br/>All Resources"]
        P_W["*:write<br/>Create · Update"]
        P_D["*:delete<br/>Remove Records"]
        P_A["*:approve<br/>Sign-off Actions"]
        P_ADMIN["admin:*<br/>System Config"]
    end

    LOGIN --> JWT --> DECODE --> RBAC
    RBAC --> ROLES

    ADMIN --> P_R & P_W & P_D & P_A & P_ADMIN
    MGR --> P_R & P_W & P_A
    TECH --> P_R & P_W
    VIEW --> P_R
    SYS --> P_R & P_W & P_D

    classDef role fill:#8E44AD,stroke:#6C3483,color:#fff
    classDef auth fill:#E67E22,stroke:#D35400,color:#fff
    classDef rbac fill:#2980B9,stroke:#1F618D,color:#fff
    classDef perm fill:#27AE60,stroke:#1E8449,color:#fff

    class ADMIN,MGR,TECH,VIEW,SYS role
    class LOGIN,JWT,DECODE auth
    class PERM,DEP rbac
    class P_R,P_W,P_D,P_A,P_ADMIN perm
```

## MVP User Stories Coverage Map

```mermaid
graph TB
    subgraph STORIES["16 MVP User Stories"]
        US1["S1: Data Connectors<br/>✅ Routes · Services · Plugins"]
        US2["S2: Command Center<br/>✅ Dashboard · Facilities · Sensors"]
        US3["S3: PPM Engine<br/>✅ Maintenance · Insights · Logs"]
        US4["S4: Query Interface<br/>✅ NLP · Voice · Multi-modal"]
        US5["S5: Ad-hoc Work Orders<br/>✅ Text-to-WO · Assignment"]
        US6["S6: Excel Native<br/>✅ Template CRUD · Sheets"]
        US7["S7: Excel Import<br/>✅ Import · Integration"]
        US8["S8: Asset Onboarding<br/>✅ QR Code · Lifecycle"]
        US9["S9: Doc Templates<br/>✅ Create · Generate · Approve"]
        US10["S10: FM Reporting<br/>✅ Schedules · Auto-generate"]
        US11["S11: Sub-Vendor Mgmt<br/>✅ Vendors · Contracts · SLAs"]
        US12["S12: WO → Commercial<br/>✅ Journey · Breakage Detection"]
        US13["S13: Manpower Registry<br/>✅ Technicians · Skills · Routing"]
        US14["S14: Inspection Reports<br/>✅ Voice · Photos · Findings"]
        US15["S15: Gamified Self-Entry<br/>✅ Points · Badges · Leaderboard"]
        US16["S16: QR Scan Insights<br/>✅ Asset Insights · AI Classify"]
    end

    classDef done fill:#27AE60,stroke:#1E8449,color:#fff
    class US1,US2,US3,US4,US5,US6,US7,US8,US9,US10,US11,US12,US13,US14,US15,US16 done
```

## Technology Stack

```mermaid
graph TB
    subgraph LANG["Language & Runtime"]
        PY["Python 3.12+"]
        ASYNC["asyncio<br/>Full Async/Await"]
    end

    subgraph FRAMEWORK["Web Framework"]
        FA["FastAPI 0.115+"]
        UV["Uvicorn<br/>ASGI Server"]
        PYD["Pydantic v2<br/>Validation & Schemas"]
    end

    subgraph AUTH_TECH["Authentication"]
        JOSE["python-jose<br/>JWT HS256"]
        PASS["passlib<br/>bcrypt Hashing"]
    end

    subgraph DATA["Data Access"]
        SA["SQLAlchemy 2.0<br/>Async ORM"]
        MOT["Motor<br/>Async MongoDB"]
        PD["Pandas<br/>CSV/Excel IO"]
    end

    subgraph INFRA["Infrastructure"]
        WS_LIB["websockets 13+<br/>Real-time"]
        HTTPX["httpx<br/>Async HTTP Client"]
        NP["NumPy<br/>Embeddings & Vectors"]
    end

    subgraph TEST["Testing"]
        PT["pytest + pytest-asyncio<br/>162 Tests Passing"]
        COV["pytest-cov<br/>Coverage"]
    end

    classDef tech fill:#2980B9,stroke:#1F618D,color:#fff
    class PY,ASYNC,FA,UV,PYD,JOSE,PASS,SA,MOT,PD,WS_LIB,HTTPX,NP,PT,COV tech
```

## Directory Structure

```
AICMMS/
├── pyproject.toml                     # Project config & dependencies
├── src/cafm/
│   ├── api/                           # ── Layer 1: Presentation ──
│   │   ├── app.py                     #   FastAPI factory + lifespan
│   │   ├── config.py                  #   API configuration
│   │   ├── auth.py                    #   JWT + RBAC
│   │   ├── dependencies.py            #   DI container
│   │   ├── middleware.py              #   CORS, rate-limit, logging
│   │   ├── websocket.py              #   Real-time event bridge
│   │   ├── routes/                    #   16 endpoint groups
│   │   │   ├── assets.py, work_orders.py, facilities.py
│   │   │   ├── inspections.py, maintenance.py, documents.py
│   │   │   ├── costs.py, gamification.py, sensors.py
│   │   │   ├── technicians.py, vendors.py, occupancy.py
│   │   │   ├── dashboard.py, query.py, connectors.py
│   │   │   └── auth.py, health.py
│   │   └── schemas/                   #   Pydantic request/response models
│   │       ├── common.py, assets.py, work_orders.py
│   │       ├── maintenance.py, technicians.py, facilities.py
│   │       ├── dashboard.py, connectors.py, vendors.py
│   │       ├── inspections.py, costs.py, sensors.py
│   │       └── documents.py, gamification.py
│   │
│   ├── services/                      # ── Layer 2: Business Logic ──
│   │   ├── asset_service.py           #   15 service modules
│   │   ├── work_order_service.py      #   encapsulating domain rules
│   │   └── ...                        #   (see full list above)
│   │
│   ├── domain/                        # ── Layer 3: Domain Model ──
│   │   ├── assets.py, work_orders.py  #   13 entity groups, 50+ models
│   │   ├── enums.py                   #   20+ shared enumerations
│   │   └── ...                        #   All inherit CAFMBaseModel
│   │
│   ├── repository/                    # ── Layer 4: Data Access ──
│   │   ├── base.py                    #   Repository<T> interface
│   │   ├── sql_repository.py          #   SQL backends (PG/MySQL/MSSQL)
│   │   ├── mongo_repository.py        #   MongoDB backend
│   │   ├── file_repository.py         #   CSV/Excel backend
│   │   └── unit_of_work.py            #   Transaction patterns
│   │
│   ├── integration/                   # ── Layer 5: Integration ──
│   │   ├── manager.py                 #   Central orchestrator
│   │   ├── pipeline.py                #   ETL: extract→transform→load
│   │   ├── scheduler.py               #   Cron-like job runner
│   │   ├── sync.py                    #   Data synchronization
│   │   └── transforms.py              #   Field mapping & transforms
│   │
│   ├── connectors/                    # ── Layer 5b: Connector Plugins ──
│   │   ├── base.py                    #   Connector + SchemaInspector ABC
│   │   ├── registry.py                #   Plugin auto-discovery
│   │   ├── lifecycle.py               #   Health checks & reconnect
│   │   ├── factory.py                 #   Instance creation
│   │   └── plugins/                   #   6 connector implementations
│   │       ├── postgresql/
│   │       ├── mysql/
│   │       ├── mssql/
│   │       ├── mongodb/
│   │       ├── csv_source/
│   │       └── excel/
│   │
│   ├── schema/                        # ── Schema Discovery ──
│   │   ├── models.py                  #   DataSourceSchema hierarchy
│   │   ├── discovery.py               #   Auto-discovery + caching
│   │   ├── diff.py                    #   Schema change detection
│   │   └── serialization.py           #   JSON serialization
│   │
│   ├── models/                        # ── Unified Data Model ──
│   │   ├── base.py                    #   CAFMBaseModel (audit, soft-delete)
│   │   ├── record.py                  #   UnifiedRecord + RecordMetadata
│   │   ├── resultset.py               #   UnifiedResultSet (paginated)
│   │   └── mapping.py                 #   Field mapping utilities
│   │
│   ├── core/                          # ── Core Infrastructure ──
│   │   ├── config.py                  #   AppConfig (env-based)
│   │   ├── events.py                  #   EventBus (pub/sub, async)
│   │   ├── exceptions.py              #   CAFMError hierarchy
│   │   ├── types.py                   #   DataSourceType, UnifiedDataType
│   │   └── logging.py                 #   Structured logging
│   │
│   └── ai/                            # ── AI Foundation ──
│       ├── interfaces.py              #   Data provider contracts
│       ├── context.py                 #   LLM context builder
│       ├── dataset_builder.py         #   Training data assembly
│       ├── embedding_store.py         #   Vector search (NumPy)
│       └── feature_store.py           #   Computed feature cache
│
└── tests/
    └── unit/                          # 162 tests passing
        ├── test_api_config.py         #   12 tests — config, JWT, RBAC
        ├── test_api_schemas.py        #   17 tests — schema validation
        ├── test_services.py           #   15 tests — core services
        ├── test_new_services.py       #   33 tests — all new services
        ├── test_new_schemas.py        #   22 tests — new schema validation
        ├── test_middleware.py         #   8 tests — error mapping
        ├── test_websocket.py          #   7 tests — connection manager
        ├── test_domain_models.py      #   10 tests — domain entities
        ├── test_transforms.py         #   8 tests — ETL transforms
        └── ... (more test modules)
```

## Design Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| Repository | `repository/base.py` | Abstract data access across SQL/Mongo/File backends |
| Service Layer | `services/*.py` | Encapsulate business rules between routes and repos |
| Dependency Injection | `api/dependencies.py` | Singleton management and testable composition |
| Plugin Registry | `connectors/registry.py` | Dynamic connector discovery via `entry_points` |
| Factory | `connectors/factory.py` | Create typed connector instances from config |
| Pub/Sub Event Bus | `core/events.py` | Decoupled inter-component communication |
| Template Method | `connectors/base.py` | Standard connector lifecycle with extension points |
| Chain of Responsibility | `integration/pipeline.py` | Composable ETL transform chains |
| Unit of Work | `repository/unit_of_work.py` | Transaction boundary management |
| Adapter | `models/mapping.py` | Unified interface over heterogeneous data sources |
| Singleton | `ConnectorRegistry`, `EventBus` | Thread-safe shared state |
| Strategy | `ai/interfaces.py` | Swappable AI data provider implementations |
