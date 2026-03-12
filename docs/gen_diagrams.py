"""Generate AICMMS Azure Architecture diagrams as PNG images.

Styled after the Accure Platform reference layout:
- Data Sources sidebar on the left
- AI capabilities across the top
- Unified Data Foundation horizontal bar
- 4 Pillar capability cards in the center
- Data stores at the bottom
- Security boundary wrapping everything
"""

from __future__ import annotations

import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from diagrams import Cluster, Diagram, Edge
from diagrams.azure.compute import ContainerApps, FunctionApps, AppServices
from diagrams.azure.database import (
    CosmosDb,
    SQLDatabases,
    CacheForRedis,
    DataFactory,
    DataLake,
)
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.integration import APIManagement, ServiceBus, LogicApps
from diagrams.azure.ml import (
    CognitiveServices,
    AzureOpenAI,
    AzureSpeechService,
    BotServices,
)
from diagrams.azure.monitor import Monitor
from diagrams.azure.network import FrontDoors
from diagrams.azure.security import KeyVaults
from diagrams.azure.storage import BlobStorage
from diagrams.azure.web import Signalr, Search
from diagrams.azure.analytics import PowerBiEmbedded
from diagrams.azure.iot import IotHub
from diagrams.onprem.client import Users, Client
from diagrams.generic.device import Mobile


# ─── Shared Styles ────────────────────────────────────────
FONT = "Helvetica"
FONT_BOLD = "Helvetica Bold"

# Color palette (soft pastels matching reference)
COL_BOUNDARY = "#F0F4FF"       # Light blue-grey boundary
COL_AI_GEN = "#EDE7F6"         # Soft purple for Generative AI
COL_AI_AGENT = "#E8F5E9"       # Soft green for Agentic AI
COL_AI_EXPERT = "#FFF3E0"      # Soft orange for Expert AI
COL_UNIFIED = "#E3F2FD"        # Blue for unified data bar
COL_PILLAR1 = "#E8F5E9"        # Green for Ingestion
COL_PILLAR2 = "#FFF3E0"        # Orange for AI/ML
COL_PILLAR3 = "#F3E5F5"        # Purple for Data/Command
COL_PILLAR4 = "#E1F5FE"        # Light blue for Field Tech
COL_DATALAKE = "#E0F2F1"       # Teal for data lake
COL_DATAWAREHOUSE = "#FFF8E1"  # Amber for data warehouse
COL_SOURCES = "#FAFAFA"        # Near-white for sources
COL_SECURITY = "#FFEBEE"       # Soft red for security
COL_PLATFORM = "#ECEFF1"       # Grey for platform bar

# Edge colors
E_BLUE = "#1565C0"
E_GREEN = "#2E7D32"
E_ORANGE = "#E65100"
E_PURPLE = "#6A1B9A"
E_TEAL = "#00695C"
E_RED = "#B71C1C"


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 1: Platform Overview (mirrors reference image layout)
# ═══════════════════════════════════════════════════════════════

def diagram_1_platform_overview():
    with Diagram(
        "",
        filename="01_aicmms_platform_overview",
        show=False,
        direction="TB",
        graph_attr={
            "fontsize": "14",
            "bgcolor": "#FFFFFF",
            "pad": "1.2",
            "nodesep": "0.8",
            "ranksep": "1.2",
            "fontname": FONT,
            "label": "",
            "splines": "ortho",
        },
    ):
        # ── Data Sources (left sidebar) ──
        with Cluster(
            "Data Sources",
            graph_attr={
                "bgcolor": COL_SOURCES,
                "fontsize": "20",
                "fontname": FONT_BOLD,
                "fontcolor": "#1565C0",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#90CAF9",
            },
        ):
            with Cluster(
                "Structured",
                graph_attr={
                    "bgcolor": "#FFFFFF",
                    "fontsize": "14",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#D32F2F",
                    "style": "rounded",
                    "penwidth": "1",
                },
            ):
                src_cmms = Client("CMMS / CAFM")
                src_erp = Client("ERP (SAP/Oracle)")
                src_excel = Client("CSV / Excel")

            with Cluster(
                "Unstructured",
                graph_attr={
                    "bgcolor": "#FFFFFF",
                    "fontsize": "14",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#7B1FA2",
                    "style": "rounded",
                    "penwidth": "1",
                },
            ):
                src_pdf = Client("PDF / Contracts")
                src_photos = Mobile("Images / Videos")
                src_voice = Mobile("Audio / Voice")

            with Cluster(
                "Semi-Structured",
                graph_attr={
                    "bgcolor": "#FFFFFF",
                    "fontsize": "14",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#00695C",
                    "style": "rounded",
                    "penwidth": "1",
                },
            ):
                src_json = Client("JSON / XML / BMS")
                src_mongo = Client("MongoDB / NoSQL")

            with Cluster(
                "Streaming & IoT",
                graph_attr={
                    "bgcolor": "#FFFFFF",
                    "fontsize": "14",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#E65100",
                    "style": "rounded",
                    "penwidth": "1",
                },
            ):
                src_iot = IotHub("IoT Sensors / BMS")
                src_bms = Client("SCADA / Controls")

        # ── AICMMS Platform Boundary ──
        with Cluster(
            "AICMMS PLATFORM  |  PRIVATE ENTERPRISE BOUNDARY",
            graph_attr={
                "bgcolor": COL_BOUNDARY,
                "fontsize": "22",
                "fontname": FONT_BOLD,
                "fontcolor": "#1565C0",
                "style": "rounded,bold",
                "penwidth": "3",
                "pencolor": "#1976D2",
            },
        ):

            # ── Row 1: AI Capabilities ──
            with Cluster(
                "Generative AI",
                graph_attr={
                    "bgcolor": COL_AI_GEN,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#4527A0",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#B39DDB",
                },
            ):
                gen_ai = AzureOpenAI("GPT-4o\nNLP · Multi-modal\nContent Generation")

            with Cluster(
                "Agentic AI",
                graph_attr={
                    "bgcolor": COL_AI_AGENT,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#2E7D32",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#A5D6A7",
                },
            ):
                agentic_ai = BotServices("Autonomous Agents\nOrchestrate Tasks\n& Workflows")

            with Cluster(
                "Expert AI",
                graph_attr={
                    "bgcolor": COL_AI_EXPERT,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#E65100",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#FFCC80",
                },
            ):
                expert_ai = CognitiveServices("FM Domain Experts\nInspection · Routing\nPredictive Maint.")

            # ── Unified Data Foundation Bar ──
            with Cluster(
                "UNIFIED DATA FOUNDATION  —  Microsoft Fabric OneLake",
                graph_attr={
                    "bgcolor": COL_UNIFIED,
                    "fontsize": "18",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#0D47A1",
                    "style": "rounded,bold",
                    "penwidth": "2",
                    "pencolor": "#42A5F5",
                },
            ):
                fabric = DataLake("OneLake\nUnified Data Lake\nAll Domains Consolidated")
                ai_search = Search("AI Search\nVector Embeddings\nKnowledge Base")
                redis = CacheForRedis("Redis Cache\nSessions · State")

            # ── Row 2: Four Pillar Cards ──
            with Cluster(
                "Data Ingestion",
                graph_attr={
                    "bgcolor": COL_PILLAR1,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#1B5E20",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#66BB6A",
                },
            ):
                p1_label = DataFactory("Ingest, clean, and\nautomate data pipelines")
                p1_ingester = CognitiveServices("Document\nIntelligence")
                p1_transformer = FunctionApps("ETL Pipeline\nTransformer")

            with Cluster(
                "AI / ML Agents",
                graph_attr={
                    "bgcolor": COL_PILLAR2,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#E65100",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#FFB74D",
                },
            ):
                p2_maint = BotServices("Maintenance\nAgent")
                p2_route = BotServices("Routing\nAgent")
                p2_report = BotServices("Reporting\nAgent")

            with Cluster(
                "Field Ops",
                graph_attr={
                    "bgcolor": COL_PILLAR4,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#01579B",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#4FC3F7",
                },
            ):
                p4_mobile = AppServices("Mobile App\nOffline · PWA")
                p4_qr = CognitiveServices("QR Scan\n& AI Vision")
                p4_gamify = FunctionApps("Gamification\nEngine")

            with Cluster(
                "FM Command Center",
                graph_attr={
                    "bgcolor": COL_PILLAR3,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#4A148C",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#CE93D8",
                },
            ):
                p3_pbi = PowerBiEmbedded("Power BI\nDashboards")
                p3_sla = Monitor("SLA Tracking\n& Alerts")
                p3_signalr = Signalr("Real-time\nUpdates")

            # ── Row 3: Data Stores ──
            with Cluster(
                "Operational Data Warehouse",
                graph_attr={
                    "bgcolor": COL_DATAWAREHOUSE,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#F57F17",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#FFD54F",
                },
            ):
                dw_sql = SQLDatabases("Azure SQL\nAssets · Work Orders\nVendors · Costs")
                dw_cosmos = CosmosDb("Cosmos DB\nIoT · Audit Trail\nReal-time State")

            with Cluster(
                "Document & Media Store",
                graph_attr={
                    "bgcolor": COL_DATALAKE,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#004D40",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#80CBC4",
                },
            ):
                dl_blob = BlobStorage("Blob Storage\nPhotos · PDFs · Voice\nReports · Templates")

            # ── Security & Governance Bar ──
            with Cluster(
                "SECURITY & GOVERNANCE",
                graph_attr={
                    "bgcolor": COL_SECURITY,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#B71C1C",
                    "style": "rounded,bold",
                    "penwidth": "2",
                    "pencolor": "#EF9A9A",
                },
            ):
                sec_entra = ActiveDirectory("Entra ID\nSSO · MFA · RBAC")
                sec_apim = APIManagement("API Management\nRate Limiting")
                sec_kv = KeyVaults("Key Vault\nSecrets · Certs")
                sec_fd = FrontDoors("Front Door\nWAF · DDoS")

            # ── Azure Platform Bar ──
            with Cluster(
                "AZURE PLATFORM",
                graph_attr={
                    "bgcolor": COL_PLATFORM,
                    "fontsize": "16",
                    "fontname": FONT_BOLD,
                    "fontcolor": "#37474F",
                    "style": "rounded",
                    "penwidth": "2",
                    "pencolor": "#90A4AE",
                },
            ):
                plat_ca = ContainerApps("Container Apps")
                plat_func = FunctionApps("Functions")
                plat_logic = LogicApps("Logic Apps")
                plat_bus = ServiceBus("Service Bus")

        # ═══ FLOWS ═══

        # Data Sources → Platform (IMPORT)
        src_cmms >> Edge(color=E_GREEN, style="bold", label="IMPORT") >> p1_label
        src_erp >> Edge(color=E_GREEN) >> p1_label
        src_excel >> Edge(color=E_GREEN) >> p1_label
        src_pdf >> Edge(color=E_PURPLE) >> p1_ingester
        src_photos >> Edge(color=E_ORANGE) >> p1_ingester
        src_voice >> Edge(color=E_ORANGE) >> gen_ai
        src_json >> Edge(color=E_TEAL) >> p1_label
        src_iot >> Edge(color=E_TEAL, style="bold") >> dw_cosmos

        # AI row connections
        gen_ai >> Edge(color=E_PURPLE, style="bold") >> agentic_ai
        agentic_ai >> Edge(color=E_ORANGE, style="bold") >> expert_ai

        # AI → Pillar cards
        gen_ai >> Edge(color=E_PURPLE, style="dashed") >> p2_maint
        agentic_ai >> Edge(color=E_GREEN, style="dashed") >> p2_route
        expert_ai >> Edge(color=E_ORANGE, style="dashed") >> p2_report

        # Ingestion → Unified Data
        p1_label >> Edge(color=E_GREEN, style="bold") >> fabric
        p1_ingester >> Edge(color=E_GREEN) >> fabric
        p1_transformer >> Edge(color=E_GREEN) >> fabric

        # Agents → Data
        p2_maint >> Edge(color=E_ORANGE) >> dw_sql
        p2_route >> Edge(color=E_ORANGE) >> dw_sql
        p2_report >> Edge(color=E_PURPLE) >> fabric

        # Command Center from data
        fabric >> Edge(color=E_BLUE, style="bold") >> p3_pbi
        dw_cosmos >> Edge(color=E_TEAL) >> p3_signalr
        p3_pbi >> Edge(color=E_BLUE) >> p3_sla

        # Field Ops connections
        p4_mobile >> Edge(color="#0277BD") >> p4_qr
        p4_mobile >> Edge(color="#0277BD") >> p4_gamify
        p4_qr >> Edge(color=E_ORANGE, style="dashed") >> ai_search

        # Unified → Data Stores
        fabric >> Edge(color=E_PURPLE, style="bold") >> dw_sql
        fabric >> Edge(color=E_TEAL) >> dl_blob

        # Security connections
        sec_fd >> Edge(color=E_RED) >> sec_entra
        sec_entra >> Edge(color=E_RED) >> sec_apim

        # Platform connections
        plat_ca >> Edge(color="#546E7A", style="dashed") >> plat_func
        plat_logic >> Edge(color="#546E7A", style="dashed") >> plat_bus

    print("  [OK] 01_aicmms_platform_overview.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 2: Pillar 1 — Multi-Modal Ingestion & Connectors
# ═══════════════════════════════════════════════════════════════

def diagram_2_ingestion():
    with Diagram(
        "",
        filename="02_pillar1_ingestion_connectors",
        show=False,
        direction="LR",
        graph_attr={
            "fontsize": "14",
            "bgcolor": "#FFFFFF",
            "pad": "1.0",
            "nodesep": "0.7",
            "ranksep": "1.4",
            "fontname": FONT,
            "label": "PILLAR 1  —  Multi-Modal Ingestion & Connectors  (Stories 1, 6, 7, 8, 13)",
            "labelloc": "b",
            "labeljust": "c",
            "fontcolor": "#1B5E20",
        },
    ):
        # ── Data Sources ──
        with Cluster(
            "Data Sources",
            graph_attr={
                "bgcolor": COL_SOURCES,
                "fontsize": "18",
                "fontname": FONT_BOLD,
                "fontcolor": "#1565C0",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#90CAF9",
            },
        ):
            with Cluster("Structured", graph_attr={"bgcolor": "#FFFFFF", "fontsize": "13", "fontname": FONT_BOLD, "fontcolor": "#D32F2F", "style": "rounded"}):
                s_cmms = Client("Existing CMMS\n/ CAFM")
                s_erp = Client("ERP System\nSAP / Oracle")
                s_csv = Client("Excel / CSV\nAsset Registers")
                s_sql = Client("SQL Databases\nPostgreSQL / MSSQL")

            with Cluster("Unstructured", graph_attr={"bgcolor": "#FFFFFF", "fontsize": "13", "fontname": FONT_BOLD, "fontcolor": "#7B1FA2", "style": "rounded"}):
                s_pdf = Client("PDFs / Contracts\nInvoices / Records")
                s_photo = Mobile("Photos / Videos\nAsset Conditions")
                s_voice = Mobile("Voice Notes\nInspection Audio")

            with Cluster("Streaming", graph_attr={"bgcolor": "#FFFFFF", "fontsize": "13", "fontname": FONT_BOLD, "fontcolor": "#E65100", "style": "rounded"}):
                s_iot = IotHub("IoT Sensors\nTemp · Humidity\nEnergy · Motion")
                s_bms = Client("BMS / SCADA\nBuilding Controls")

        # ── Connector Plugins ──
        with Cluster(
            "6 Connector Plugins",
            graph_attr={
                "bgcolor": "#E8F5E9",
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#1B5E20",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#66BB6A",
            },
        ):
            adf = DataFactory("Azure Data Factory\nETL Orchestration\n6 Source Adapters")

            with Cluster("Plugin Registry", graph_attr={"bgcolor": "#C8E6C9", "fontsize": "12", "fontname": FONT_BOLD, "style": "rounded"}):
                plug_pg = FunctionApps("PostgreSQL")
                plug_mysql = FunctionApps("MySQL")
                plug_mssql = FunctionApps("MS SQL")
                plug_mongo = FunctionApps("MongoDB")
                plug_csv = FunctionApps("CSV / Excel")
                plug_rest = FunctionApps("REST API")

        # ── AI Processing ──
        with Cluster(
            "AI Document Processing",
            graph_attr={
                "bgcolor": "#FFF3E0",
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#E65100",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#FFB74D",
            },
        ):
            doc_intel = CognitiveServices("AI Document Intelligence\nContract Extraction\nInvoice Parsing\nForm Recognition")
            ai_vision = CognitiveServices("Azure AI Vision\nAsset Photo Analysis\nCondition Assessment\nAuto-tag & Classify")
            speech = AzureSpeechService("AI Speech\nVoice Transcription\nMulti-language")

        # ── Transformation ──
        with Cluster(
            "Transform & Validate",
            graph_attr={
                "bgcolor": "#E3F2FD",
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#0D47A1",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#42A5F5",
            },
        ):
            etl = FunctionApps("ETL Pipeline\nSchema Mapping\nType Casting\nDeduplication")
            validate = FunctionApps("Validation\nBusiness Rules\nData Quality\nConflict Resolution")

        # ── Storage Targets ──
        with Cluster(
            "Storage Targets",
            graph_attr={
                "bgcolor": "#F3E5F5",
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#4A148C",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#CE93D8",
            },
        ):
            st_sql = SQLDatabases("Azure SQL\nStructured Data")
            st_cosmos = CosmosDb("Cosmos DB\nIoT Time-series")
            st_blob = BlobStorage("Blob Storage\nMedia & Docs")
            st_fabric = DataLake("Fabric OneLake\nUnified Lake")

        # ═══ FLOWS ═══
        s_cmms >> Edge(color=E_GREEN, style="bold") >> adf
        s_erp >> Edge(color=E_GREEN, style="bold") >> adf
        s_csv >> Edge(color=E_GREEN) >> adf
        s_sql >> Edge(color=E_GREEN) >> adf
        s_bms >> Edge(color=E_TEAL) >> adf

        s_pdf >> Edge(color=E_PURPLE, style="bold") >> doc_intel
        s_photo >> Edge(color=E_ORANGE, style="bold") >> ai_vision
        s_voice >> Edge(color=E_ORANGE) >> speech

        s_iot >> Edge(color=E_TEAL, style="bold") >> st_cosmos

        adf >> Edge(color=E_GREEN, style="bold") >> etl
        doc_intel >> Edge(color=E_PURPLE) >> etl
        ai_vision >> Edge(color=E_ORANGE) >> etl
        speech >> Edge(color=E_ORANGE) >> etl

        etl >> Edge(color=E_BLUE) >> validate

        validate >> Edge(color=E_PURPLE, style="bold") >> st_sql
        validate >> Edge(color=E_PURPLE, style="bold") >> st_fabric
        validate >> Edge(color=E_PURPLE) >> st_blob

    print("  [OK] 02_pillar1_ingestion_connectors.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 3: Pillar 2 — AI Agentic Layer
# ═══════════════════════════════════════════════════════════════

def diagram_3_ai_agentic():
    with Diagram(
        "",
        filename="03_pillar2_ai_agentic_layer",
        show=False,
        direction="TB",
        graph_attr={
            "fontsize": "14",
            "bgcolor": "#FFFFFF",
            "pad": "1.0",
            "nodesep": "0.8",
            "ranksep": "1.0",
            "fontname": FONT,
            "label": "PILLAR 2  —  AI Agentic Layer & Autonomous Workflows  (Stories 3, 4, 5, 9, 10)",
            "labelloc": "b",
            "labeljust": "c",
            "fontcolor": "#E65100",
        },
    ):
        # ── Multi-Modal Input ──
        with Cluster(
            "Multi-Modal Input",
            graph_attr={
                "bgcolor": COL_UNIFIED,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#0D47A1",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#42A5F5",
            },
        ):
            in_text = Users("Text Query\n'Show overdue WOs'\n'Schedule HVAC PM'")
            in_voice = Mobile("Voice Command\nSpeech-to-Text\nMulti-language")
            in_photo = Mobile("Photo / Document\nClassify Damage\nExtract Data")

        # ── Azure AI Foundry ──
        with Cluster(
            "Azure AI Foundry  (GPT-4o)",
            graph_attr={
                "bgcolor": COL_AI_GEN,
                "fontsize": "18",
                "fontname": FONT_BOLD,
                "fontcolor": "#4527A0",
                "style": "rounded,bold",
                "penwidth": "2",
                "pencolor": "#B39DDB",
            },
        ):
            orchestrator = AzureOpenAI("AI Orchestrator\nIntent Detection\nEntity Extraction\nContext Building")

            with Cluster("Supporting Services", graph_attr={"bgcolor": "#D1C4E9", "fontsize": "12", "fontname": FONT_BOLD, "style": "rounded"}):
                nlp = CognitiveServices("NLP Processing\nMulti-language\nSentiment")
                rag = Search("RAG Pipeline\nVector Search\nKnowledge Base")
                speech = AzureSpeechService("Speech Service\nSTT / TTS")

        # ── 5 Autonomous Agents ──
        with Cluster(
            "5 Autonomous AI Agents",
            graph_attr={
                "bgcolor": COL_AI_EXPERT,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#E65100",
                "style": "rounded,bold",
                "penwidth": "2",
                "pencolor": "#FFB74D",
            },
        ):
            a_wo = BotServices("Work Order\nAgent\nAd-hoc Creation\nPriority Assignment")
            a_route = BotServices("Routing\nAgent\nSkill Matching\nWorkload Balance")
            a_maint = BotServices("Maintenance\nAgent\nPPM Scheduling\nFailure Prediction")
            a_report = BotServices("Reporting\nAgent\nAuto-generate\nScheduled Delivery")
            a_inspect = BotServices("Inspection\nAgent\nAI Classification\nAction Triggering")

        # ── Workflow Automation ──
        with Cluster(
            "Workflow Automation",
            graph_attr={
                "bgcolor": COL_PILLAR1,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#1B5E20",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#66BB6A",
            },
        ):
            logic = LogicApps("Logic Apps\nWorkflow Orchestration\nConditional Routing")
            bus = ServiceBus("Service Bus\nAsync Event Queue\nReliable Delivery")
            funcs = FunctionApps("Azure Functions\nNotifications\nEmail · Push · SMS")

        # ── Downstream Actions ──
        with Cluster(
            "Automated Downstream Actions",
            graph_attr={
                "bgcolor": COL_DATAWAREHOUSE,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#F57F17",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#FFD54F",
            },
        ):
            act_wo = SQLDatabases("Create / Update\nWork Order")
            act_vendor = Client("Vendor\nNotification")
            act_invoice = Client("Generate\nInvoice / PO")
            act_report = BlobStorage("Store FM\nReport")
            act_ppm = SQLDatabases("Update PPM\nSchedule")

        # ═══ FLOWS ═══
        in_text >> Edge(color=E_ORANGE, style="bold") >> orchestrator
        in_voice >> Edge(color=E_ORANGE, style="bold") >> orchestrator
        in_photo >> Edge(color=E_ORANGE, style="bold") >> orchestrator

        orchestrator >> Edge(color=E_PURPLE, style="dashed") >> nlp
        orchestrator >> Edge(color=E_PURPLE, style="dashed") >> rag
        orchestrator >> Edge(color=E_PURPLE, style="dashed") >> speech

        orchestrator >> Edge(color="#F57C00", style="bold") >> a_wo
        orchestrator >> Edge(color="#F57C00", style="bold") >> a_route
        orchestrator >> Edge(color="#F57C00", style="bold") >> a_maint
        orchestrator >> Edge(color="#F57C00", style="bold") >> a_report
        orchestrator >> Edge(color="#F57C00", style="bold") >> a_inspect

        a_wo >> Edge(color=E_GREEN) >> logic
        a_route >> Edge(color=E_GREEN) >> logic
        a_maint >> Edge(color=E_GREEN) >> logic
        a_report >> Edge(color=E_GREEN) >> logic
        a_inspect >> Edge(color=E_GREEN) >> logic

        logic >> Edge(color=E_GREEN) >> bus
        bus >> Edge(color=E_GREEN) >> funcs

        logic >> Edge(color=E_PURPLE, style="bold") >> act_wo
        logic >> Edge(color=E_PURPLE) >> act_vendor
        logic >> Edge(color=E_PURPLE) >> act_invoice
        logic >> Edge(color=E_PURPLE) >> act_report
        logic >> Edge(color=E_PURPLE) >> act_ppm

    print("  [OK] 03_pillar2_ai_agentic_layer.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 4: Pillar 3 — Data Foundation & FM Command Center
# ═══════════════════════════════════════════════════════════════

def diagram_4_data_foundation():
    with Diagram(
        "",
        filename="04_pillar3_data_command_center",
        show=False,
        direction="TB",
        graph_attr={
            "fontsize": "14",
            "bgcolor": "#FFFFFF",
            "pad": "1.0",
            "nodesep": "0.7",
            "ranksep": "1.0",
            "fontname": FONT,
            "label": "PILLAR 3  —  Data Foundation & FM Command Center  (Stories 2, 11, 12)",
            "labelloc": "b",
            "labeljust": "c",
            "fontcolor": "#4A148C",
        },
    ):
        # ── Domain Databases ──
        with Cluster(
            "Domain Data Stores",
            graph_attr={
                "bgcolor": COL_PILLAR3,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#4A148C",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#CE93D8",
            },
        ):
            with Cluster(
                "Structured — Azure SQL",
                graph_attr={"bgcolor": "#E1BEE7", "fontsize": "13", "fontname": FONT_BOLD, "style": "rounded"},
            ):
                db_assets = SQLDatabases("Assets & Lifecycle\n50+ fields\nCondition Scoring")
                db_wo = SQLDatabases("Work Orders\nAd-hoc · PPM\nStatus Tracking")
                db_vendor = SQLDatabases("Vendors & Contracts\nSLAs · Performance\nCompliance")
                db_cost = SQLDatabases("Costs & Finance\nExpenses · Invoices\nBudgets · POs")

            with Cluster(
                "Real-time — Cosmos DB",
                graph_attr={"bgcolor": "#B2DFDB", "fontsize": "13", "fontname": FONT_BOLD, "style": "rounded"},
            ):
                db_iot = CosmosDb("IoT Telemetry\nSensor Readings\nThreshold Alerts")
                db_audit = CosmosDb("Audit Trail\nAll Operations\nChange History")
                db_live = CosmosDb("Live Metadata\nTech Locations\nWO Status")

            with Cluster(
                "Unstructured — Blob Storage",
                graph_attr={"bgcolor": "#FFE0B2", "fontsize": "13", "fontname": FONT_BOLD, "style": "rounded"},
            ):
                db_photos = BlobStorage("Inspection Photos\nAsset Images")
                db_voice = BlobStorage("Voice Recordings\nTranscriptions")
                db_docs = BlobStorage("Documents\nExcel · Reports")

        # ── Unified Data Layer ──
        with Cluster(
            "Unified Data Layer",
            graph_attr={
                "bgcolor": COL_UNIFIED,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#0D47A1",
                "style": "rounded,bold",
                "penwidth": "2",
                "pencolor": "#42A5F5",
            },
        ):
            fabric = DataLake("Microsoft Fabric OneLake\nUnified Data Lake\nAll Domains Consolidated")
            search = Search("Azure AI Search\nFull-text + Vector\nAsset Knowledge Base")
            cache = CacheForRedis("Redis Cache\nDashboard State\nSession Data")

        # ── FM Command Center ──
        with Cluster(
            "FM Command Center",
            graph_attr={
                "bgcolor": COL_PILLAR4,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#01579B",
                "style": "rounded,bold",
                "penwidth": "2",
                "pencolor": "#4FC3F7",
            },
        ):
            pbi = PowerBiEmbedded("Power BI Embedded\nInteractive Dashboards")
            signalr = Signalr("SignalR Service\nReal-time Push")

            with Cluster(
                "Dashboard Widgets",
                graph_attr={"bgcolor": "#B3E5FC", "fontsize": "13", "fontname": FONT_BOLD, "style": "rounded"},
            ):
                w_sla = Monitor("SLA Tracking\nResponse Time\nVendor KPIs")
                w_asset = Monitor("Asset Lifecycle\nCondition · Age\nRisk Scoring")
                w_profit = Monitor("Profitability\nCost vs Budget\nWO→Invoice")
                w_occupy = Monitor("Occupancy\nHeatmaps\nUtilization")

        # ═══ FLOWS ═══
        db_assets >> Edge(color=E_PURPLE) >> fabric
        db_wo >> Edge(color=E_PURPLE) >> fabric
        db_vendor >> Edge(color=E_PURPLE) >> fabric
        db_cost >> Edge(color=E_PURPLE) >> fabric

        db_iot >> Edge(color=E_TEAL) >> fabric
        db_audit >> Edge(color=E_TEAL) >> fabric

        db_photos >> Edge(color=E_ORANGE) >> search
        db_docs >> Edge(color=E_ORANGE) >> search

        fabric >> Edge(color=E_BLUE, style="bold") >> pbi
        fabric >> Edge(color=E_BLUE) >> search
        db_live >> Edge(color=E_TEAL, style="bold") >> signalr
        cache >> Edge(color=E_BLUE, style="dashed") >> pbi

        pbi >> Edge(color=E_BLUE) >> w_sla
        pbi >> Edge(color=E_BLUE) >> w_asset
        pbi >> Edge(color=E_BLUE) >> w_profit
        pbi >> Edge(color=E_BLUE) >> w_occupy
        signalr >> Edge(color=E_TEAL, style="bold") >> w_sla

    print("  [OK] 04_pillar3_data_command_center.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 5: Pillar 4 — Field Technician Experience
# ═══════════════════════════════════════════════════════════════

def diagram_5_field_tech():
    with Diagram(
        "",
        filename="05_pillar4_field_technician",
        show=False,
        direction="TB",
        graph_attr={
            "fontsize": "14",
            "bgcolor": "#FFFFFF",
            "pad": "1.0",
            "nodesep": "0.7",
            "ranksep": "1.0",
            "fontname": FONT,
            "label": "PILLAR 4  —  Field Technician Experience  (Stories 14, 15, 16)",
            "labelloc": "b",
            "labeljust": "c",
            "fontcolor": "#01579B",
        },
    ):
        # ── Technician ──
        tech = Mobile("Field Technician\nMobile App")

        # ── Mobile Frontend ──
        with Cluster(
            "Mobile-First Frontend",
            graph_attr={
                "bgcolor": COL_PILLAR4,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#01579B",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#4FC3F7",
            },
        ):
            app = AppServices("Azure App Service\nPWA · Offline Sync\nResponsive Design")

            with Cluster(
                "Story 16: QR Code & Insights",
                graph_attr={"bgcolor": "#B3E5FC", "fontsize": "13", "fontname": FONT_BOLD, "style": "rounded"},
            ):
                qr = CognitiveServices("Azure AI Vision\nQR Code Scanning\nAsset Identification")
                insights = Search("AI Search\nTechnical Insights\nHistory & Manuals")

            with Cluster(
                "Story 14: Inspection Workflow",
                graph_attr={"bgcolor": "#B3E5FC", "fontsize": "13", "fontname": FONT_BOLD, "style": "rounded"},
            ):
                voice_in = AzureSpeechService("Voice Input\nSpeech-to-Text\nMulti-language")
                photo_in = CognitiveServices("Photo Capture\nCondition Evidence\nAI Classification")
                prefill = FunctionApps("50% Pre-fill\nPrevious Data\nAsset Defaults")

            with Cluster(
                "Story 15: Gamification Engine",
                graph_attr={"bgcolor": "#C8E6C9", "fontsize": "13", "fontname": FONT_BOLD, "style": "rounded"},
            ):
                gam = FunctionApps("Gamification Service\nImpact Points\n6 Levels (Rookie→Legend)")
                leader = Signalr("Live Leaderboard\nReal-time Rankings\nTeam Competition")
                badges = CosmosDb("Badges & Streaks\nAchievements\nReward Tracking")

        # ── AI Classification ──
        with Cluster(
            "AI Classification Engine",
            graph_attr={
                "bgcolor": COL_AI_GEN,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#4527A0",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#B39DDB",
            },
        ):
            ai_class = AzureOpenAI("Azure AI Foundry\nInspection Classification\nSeverity Assessment\nAction Recommendation")

        # ── Triggered Actions ──
        with Cluster(
            "Automated Triggered Actions",
            graph_attr={
                "bgcolor": COL_PILLAR1,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#1B5E20",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#66BB6A",
            },
        ):
            act_wo = SQLDatabases("Auto-create\nWork Order")
            act_ppm = SQLDatabases("Update PPM\nSchedule")
            act_notify = FunctionApps("Notify Manager\nPush · Email")
            act_points = CosmosDb("Award Impact\nPoints")

        # ═══ FLOWS ═══
        tech >> Edge(color="#0277BD", style="bold") >> app

        app >> Edge(color="#0277BD") >> qr
        qr >> Edge(color="#0277BD") >> insights

        app >> Edge(color=E_ORANGE) >> voice_in
        app >> Edge(color=E_ORANGE) >> photo_in
        app >> Edge(color=E_GREEN) >> prefill

        voice_in >> Edge(color=E_ORANGE, style="bold") >> ai_class
        photo_in >> Edge(color=E_ORANGE, style="bold") >> ai_class

        app >> Edge(color=E_GREEN) >> gam
        gam >> Edge(color=E_GREEN) >> leader
        gam >> Edge(color=E_GREEN) >> badges

        ai_class >> Edge(color=E_GREEN, style="bold") >> act_wo
        ai_class >> Edge(color=E_GREEN) >> act_ppm
        ai_class >> Edge(color=E_GREEN) >> act_notify
        gam >> Edge(color=E_GREEN) >> act_points

    print("  [OK] 05_pillar4_field_technician.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 6: End-to-End Flow (All 16 User Stories)
# ═══════════════════════════════════════════════════════════════

def diagram_6_e2e_flow():
    with Diagram(
        "",
        filename="06_end_to_end_flow",
        show=False,
        direction="LR",
        graph_attr={
            "fontsize": "14",
            "bgcolor": "#FFFFFF",
            "pad": "1.0",
            "nodesep": "0.6",
            "ranksep": "1.4",
            "fontname": FONT,
            "label": "AICMMS  —  End-to-End Architecture Flow  (All 16 User Stories)",
            "labelloc": "b",
            "labeljust": "c",
            "fontcolor": "#0D47A1",
        },
    ):
        # ── Entry Points ──
        with Cluster(
            "Entry Points",
            graph_attr={
                "bgcolor": COL_UNIFIED,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#0D47A1",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#42A5F5",
            },
        ):
            ep_mgr = Users("FM Manager\nWeb Dashboard")
            ep_tech = Mobile("Technician\nMobile App")
            ep_vendor = Client("Sub-Vendor\nPortal")
            ep_iot = IotHub("IoT / BMS\nSensors")
            ep_legacy = Client("Legacy CMMS\nERP · Excel")

        # ── Security Gateway ──
        with Cluster(
            "Security Gateway",
            graph_attr={
                "bgcolor": COL_SECURITY,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#B71C1C",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#EF9A9A",
            },
        ):
            fd = FrontDoors("Front Door\nWAF · DDoS")
            entra = ActiveDirectory("Entra ID\nSSO · MFA\n5 RBAC Roles")
            apim = APIManagement("API Management\nRate Limit\nPolicies")

        # ── Application Layer ──
        with Cluster(
            "Application Layer (Container Apps)",
            graph_attr={
                "bgcolor": COL_PILLAR1,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#1B5E20",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#66BB6A",
            },
        ):
            api = ContainerApps("FastAPI Backend\n16 Route Groups\n80+ Endpoints\n15 Services")

        # ── AI Engine ──
        with Cluster(
            "AI Engine",
            graph_attr={
                "bgcolor": COL_AI_GEN,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#4527A0",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#B39DDB",
            },
        ):
            ai = AzureOpenAI("Azure OpenAI\nGPT-4o")
            agents = BotServices("AI Agents\nMaint · Route\nReport · Inspect")
            vision = CognitiveServices("AI Vision\n+ Doc Intel")
            speech_svc = AzureSpeechService("Speech\nService")

        # ── Automation ──
        with Cluster(
            "Automation & Orchestration",
            graph_attr={
                "bgcolor": COL_AI_EXPERT,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#E65100",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#FFB74D",
            },
        ):
            logic = LogicApps("Logic Apps\nWorkflows")
            funcs = FunctionApps("Functions\nScheduler\nGamification")
            bus = ServiceBus("Service Bus\nEvent Queue")

        # ── Data Foundation ──
        with Cluster(
            "Data Foundation",
            graph_attr={
                "bgcolor": COL_PILLAR3,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#4A148C",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#CE93D8",
            },
        ):
            sql = SQLDatabases("Azure SQL\nCore Data")
            cosmos = CosmosDb("Cosmos DB\nIoT · Audit")
            blob = BlobStorage("Blob Storage\nMedia · Docs")
            fabric = DataLake("Fabric OneLake\nUnified Lake")
            search = Search("AI Search\nKnowledge")
            redis_c = CacheForRedis("Redis\nCache")

        # ── Outputs ──
        with Cluster(
            "Output & Insights",
            graph_attr={
                "bgcolor": COL_PILLAR4,
                "fontsize": "16",
                "fontname": FONT_BOLD,
                "fontcolor": "#01579B",
                "style": "rounded",
                "penwidth": "2",
                "pencolor": "#4FC3F7",
            },
        ):
            pbi = PowerBiEmbedded("Power BI\nCommand Center")
            signalr = Signalr("SignalR\nLive Updates")
            reports = BlobStorage("Generated\nReports")
            notif = FunctionApps("Notifications\nEmail · Push")

        # ═══ FLOWS ═══

        # Entry → Security
        ep_mgr >> Edge(color=E_BLUE, style="bold") >> fd
        ep_tech >> Edge(color=E_BLUE, style="bold") >> fd
        ep_vendor >> Edge(color=E_BLUE) >> fd
        fd >> Edge(color=E_RED) >> entra
        entra >> Edge(color=E_RED) >> apim

        # Legacy/IoT direct
        ep_legacy >> Edge(color=E_GREEN) >> api
        ep_iot >> Edge(color=E_TEAL) >> cosmos

        # Security → App
        apim >> Edge(color=E_GREEN, style="bold") >> api

        # App → AI
        api >> Edge(color=E_ORANGE, style="bold") >> ai
        ai >> Edge(color=E_ORANGE) >> agents
        api >> Edge(color=E_ORANGE, style="dashed") >> speech_svc
        api >> Edge(color=E_ORANGE, style="dashed") >> vision

        # App → Automation
        api >> Edge(color="#F57C00") >> bus
        bus >> Edge(color="#F57C00") >> funcs
        agents >> Edge(color=E_ORANGE) >> logic
        logic >> Edge(color="#F57C00") >> funcs

        # App → Data
        api >> Edge(color=E_PURPLE, style="bold") >> sql
        api >> Edge(color=E_PURPLE) >> cosmos
        api >> Edge(color=E_PURPLE) >> blob
        api >> Edge(color=E_PURPLE, style="dashed") >> redis_c

        # Data → Unified
        sql >> Edge(color=E_PURPLE, style="dashed") >> fabric
        cosmos >> Edge(color=E_PURPLE, style="dashed") >> fabric
        blob >> Edge(color=E_PURPLE, style="dashed") >> search

        # Data → Output
        fabric >> Edge(color=E_BLUE, style="bold") >> pbi
        cosmos >> Edge(color=E_TEAL) >> signalr
        funcs >> Edge(color="#F57C00") >> reports
        funcs >> Edge(color="#F57C00") >> notif

    print("  [OK] 06_end_to_end_flow.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generating AICMMS Architecture Diagrams (Platform Edition)...\n")

    diagram_1_platform_overview()
    diagram_2_ingestion()
    diagram_3_ai_agentic()
    diagram_4_data_foundation()
    diagram_5_field_tech()
    diagram_6_e2e_flow()

    print("\nAll 6 diagrams generated successfully!")
    print("Location: C:\\CAFM\\docs\\*.png")
