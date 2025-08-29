# Universal Web Scraper - Technical Portfolio

[![CI/CD Pipeline](https://github.com/tsrdatatech/web-scrapers-python/actions/workflows/ci.yml/badge.svg)](https://github.com/tsrdatatech/web-scrapers-python/actions/workflows/ci.yml)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io-blue?logo=docker)](https://github.com/tsrdatatech/web-scrapers-python/pkgs/container/web-scrapers-python)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A sophisticated, production-ready web scraping framework demonstrating advanced Python architecture patterns, comprehensive testing practices, and enterprise-level software engineering.

> **Portfolio Project**: This repository showcases professional software development skills including clean architecture, test-driven development, CI/CD implementation, and modern Python best practices.

## 🎯 Technical Highlights

- **Clean Architecture**: Plugin-based system with SOLID principles
- **Production Ready**: Comprehensive error handling, logging, and monitoring
- **Test-Driven Development**: 26+ automated tests with CI/CD integration
- **Type Safety**: Full mypy compliance with strict type checking
- **Modern Python**: Async/await, Pydantic v2, dependency injection patterns
- **DevOps Integration**: GitHub Actions, automated quality checks, multi-environment testing

## 🏗️ Architecture Overview

This project demonstrates enterprise-level software design patterns:

- **Abstract Factory Pattern**: Dynamic parser creation and registration
- **Strategy Pattern**: Runtime parser selection based on URL analysis  
- **Template Method Pattern**: Extensible base parser with customizable hooks
- **Dependency Injection**: Registry-based component management
- **Observer Pattern**: Event-driven logging and monitoring

## 🚀 Technical Stack

- **AI/ML Framework**: LangChain with prompt engineering and structured output parsing
- **Database**: Apache Cassandra for distributed data storage and deduplication
- **Browser Automation**: Crawlee + Playwright for sophisticated queue management
- **Data Validation**: Pydantic v2 with advanced type checking and serialization
- **Content Extraction**: Multi-method approach (Newspaper3k + Trafilatura + custom)
- **Async Architecture**: Modern Python async/await patterns throughout
- **Structured Logging**: Loguru with contextual error tracking
- **Testing Framework**: Pytest with comprehensive coverage strategies
- **Containerization**: Multi-stage Docker builds with production optimization
- **CI/CD Pipeline**: GitHub Actions with automated testing, security scanning, and deployment

## 📚 Professional Skills Demonstrated

### Software Architecture
- **Plugin Architecture**: Extensible parser system following Open/Closed Principle
- **Dependency Injection**: Registry-based component management
- **Strategy Pattern**: Dynamic parser selection based on URL analysis
- **Abstract Base Classes**: Template method pattern for consistent behavior
- **Separation of Concerns**: Clear boundaries between parsing, validation, and output

### Python Expertise  
- **Type Safety**: Full mypy compliance with strict typing
- **Async Programming**: Efficient concurrent processing with proper error handling
- **Modern Features**: Context managers, decorators, dataclasses, and type hints
- **Data Validation**: Runtime type checking with Pydantic schemas
- **Error Handling**: Comprehensive exception management with graceful degradation

### AI/ML Engineering with LangChain
- **Content Analysis**: AI-powered article summarization and sentiment analysis
- **Topic Classification**: Automated topic extraction and entity recognition
- **Quality Assessment**: Intelligent content quality scoring and readability analysis
- **Prompt Engineering**: Sophisticated LangChain prompt templates and output parsing
- **Fallback Systems**: Graceful degradation when AI services are unavailable
- **Mock Integration**: Development-friendly mock LLM for testing and demonstration

### Advanced Kubernetes Orchestration
- **Batch Processing**: Enterprise-grade job orchestration similar to AWS Step Functions + Batch
- **Auto-scaling**: Dynamic resource allocation with horizontal and vertical scaling
- **Job Management**: Sophisticated job lifecycle management with automatic retries
- **Monitoring**: Built-in metrics, structured logging, and health checks
- **Security**: Pod security standards, RBAC, and minimal privilege execution
- **Reliability**: Failure recovery, resource cleanup, and graceful degradation

### Distributed Database Engineering
- **Cassandra Integration**: High-performance, scalable NoSQL database for web scraping data
- **Data Deduplication**: Intelligent URL and content duplicate detection and prevention  
- **Dynamic Seed Management**: Database-driven crawler seed URL management and prioritization
- **Time-Series Analytics**: Crawl statistics, performance metrics, and historical data tracking
- **Content Versioning**: Track article changes over time with automated change detection
- **Horizontal Scaling**: Distributed architecture supporting multi-node deployments

### Testing & Quality Assurance
- **Test-Driven Development**: 26+ automated tests covering multiple scenarios
- **Integration Testing**: End-to-end workflow validation
- **Continuous Integration**: GitHub Actions with multi-Python version testing
- **Code Quality**: Automated linting, formatting, and security scanning
- **Documentation**: Comprehensive inline documentation and usage examples

### DevOps & Production Practices
- **CI/CD Pipeline**: Automated testing, quality checks, and deployment
- **Containerization**: Multi-stage Docker builds with security hardening
- **Environment Management**: Poetry for dependency management
- **Logging & Monitoring**: Structured logging with contextual error tracking
- **Configuration Management**: Flexible configuration with environment support
- **Security**: Dependency scanning and vulnerability assessment
- **Container Registry**: Automated builds with GitHub Container Registry
- **Multi-platform Support**: ARM64 and AMD64 container builds

## 🏛️ Core Features

- **AI-Enhanced Content Analysis**: LangChain-powered summarization, sentiment analysis, and topic classification
- **Distributed Database Storage**: Cassandra integration with deduplication and analytics
- **Multi-Parser Architecture**: Automatic parser selection based on URL fingerprinting
- **Advanced Kubernetes Orchestration**: Enterprise-grade batch processing with auto-scaling
- **Production Pipelines**: Complete CI/CD with automated testing, building, and deployment
- **Container Orchestration**: Kubernetes-ready with sophisticated job management
- **Type-Safe Data Models**: Pydantic v2 schemas with comprehensive validation
- **Async Content Extraction**: High-performance processing with Playwright automation
- **Enterprise Monitoring**: Structured logging with contextual error tracking

## 💻 Implementation Details

### Parser Registry System
```python
# Automatic parser discovery and registration
@dataclass
class BaseParser:
    """Abstract base implementing Template Method pattern"""
    
    async def can_parse(self, url: str) -> bool:
        """Strategy pattern for runtime parser selection"""
        
    async def parse(self, page: Page, context: dict) -> BaseModel:
        """Core extraction logic with type safety"""
```

### AI-Powered Content Analysis  
```python
# LangChain integration for intelligent content analysis
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import FakeListLLM

class AdvancedContentAnalyzer:
    def __init__(self):
        self.summary_prompt = PromptTemplate(
            input_variables=["title", "content"],
            template="Analyze this article and provide a concise summary..."
        )
        
    async def analyze_article(self, article: NewsArticle) -> ContentAnalysis:
        """AI-powered analysis with sentiment, topics, and quality scoring"""
        analysis = await self.llm.ainvoke({
            "title": article.title, 
            "content": article.content
        })
        return ContentAnalysis(
            summary=analysis.summary,
            sentiment=analysis.sentiment,
            topics=analysis.topics,
            quality_score=self.calculate_quality_score(article)
        )
```

### Data Validation Pipeline
```python
# Pydantic v2 schema with advanced validation
class NewsArticle(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10)
    url: HttpUrl
    published_date: Optional[datetime] = None
    author: Optional[str] = Field(None, max_length=200)
    ai_analysis: Optional[Dict[str, Any]] = None  # AI insights
    
    @field_validator('content')
    @classmethod
    def validate_content_quality(cls, v: str) -> str:
        # Custom business logic validation
        return v.strip()
```

## ☸️ Kubernetes Orchestration

Advanced batch processing system using pure Kubernetes primitives:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Orchestration                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │ Batch           │    │ CronJob          │    │ Manual      │ │
│  │ Orchestrator    │───▶│ Schedulers       │    │ Jobs        │ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
│           │                                              │       │
│           ▼                                              ▼       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Kubernetes Job Execution Layer                │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │ │
│  │ │ Scraper     │ │ Scraper     │ │ Scraper     │ │   ...   │ │ │
│  │ │ Job Pod 1   │ │ Job Pod 2   │ │ Job Pod 3   │ │         │ │ │
│  │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Orchestration Features
- **Batch Processing**: URL batching with configurable chunk sizes
- **Job Lifecycle Management**: Automatic creation, monitoring, and cleanup
- **Failure Recovery**: Intelligent retry logic with exponential backoff
- **Resource Management**: Dynamic scaling and resource optimization
- **Security**: Pod security standards and RBAC implementation
- **Monitoring**: Structured logging, metrics, and health checks

### Quick Deploy
```bash
# Deploy complete orchestration system
make deploy

# Monitor batch processing
make status
make logs

# Scale operations
make scale-up
make job-batch
```

## 🏗️ System Architecture

```
src/
├── main.py                 # Application entry point
├── orchestrator.py         # Kubernetes batch orchestrator
├── routes.py              # Crawlee request routing logic
├── core/
│   ├── base_parser.py     # Abstract parser base class
│   ├── logger.py          # Structured logging configuration
│   ├── parser_registry.py # Dynamic parser discovery
│   ├── parser_manager.py  # Parser selection strategy
│   ├── proxy_config.py    # Proxy management system
│   └── seeds.py           # Input processing pipeline
├── parsers/
│   ├── generic_news.py    # Universal news extraction
│   └── weibo.py           # Social media specialized parser
└── schemas/
    └── news.py            # Type-safe data models

deployment/kubernetes/
├── batch-orchestrator.yaml    # Orchestrator deployment
├── job-template.yaml         # Batch job templates
├── cronjobs.yaml            # Scheduled operations
├── orchestrator-config.yaml # RBAC and configuration
└── deploy.sh               # Automated deployment
```

## 🔬 Testing Framework

Comprehensive test coverage demonstrating TDD practices:

- **26+ Automated Tests**: Unit, integration, and end-to-end coverage
- **Multi-Python Support**: Testing matrix across Python 3.9-3.12
- **Mock Strategies**: Isolated testing with Playwright simulation
- **CI Integration**: Automated testing on every commit

### Test Architecture
```python
# Example: Parser validation testing
@pytest.mark.asyncio
async def test_parser_discovery():
    """Validates dynamic parser registration"""
    registry = ParserRegistry()
    parsers = await registry.discover_parsers()
    assert len(parsers) > 0
    
@pytest.mark.asyncio  
async def test_type_safety():
    """Ensures Pydantic schema compliance"""
    result = await parser.parse(mock_page, context)
    assert isinstance(result, NewsArticle)
    assert result.model_validate(result.model_dump())
```

## 🚢 DevOps & Deployment

### Container Strategy
- **Multi-stage Docker builds** optimized for production
- **Security hardening** with non-root user execution
- **Multi-platform support** (ARM64/AMD64) via GitHub Actions
- **Kubernetes manifests** for cloud-native deployment

### CI/CD Pipeline
```yaml
# Automated workflow demonstrating enterprise practices
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Build multi-platform image
      - name: Security vulnerability scan
      - name: Publish to GitHub Container Registry
```

### Production Architecture
- **Kubernetes deployment** with configurable replicas
- **Resource management** with requests/limits
- **Environment configuration** via ConfigMaps
- **Service exposure** with load balancing

## 📈 Performance & Monitoring

- **Async Processing**: Concurrent request handling with Playwright
- **Queue Management**: Crawlee-based request deduplication  
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Error Recovery**: Graceful failure handling with retry logic
- **Resource Optimization**: Memory-efficient content extraction

## 🔧 Technical Keywords

`Python` • `Apache Cassandra` • `Distributed Systems` • `LangChain` • `AI/ML Engineering` • `Async/Await` • `Pydantic` • `Playwright` • `Docker` • `Kubernetes` • `GitHub Actions` • `Test-Driven Development` • `Clean Architecture` • `Design Patterns` • `Type Safety` • `CI/CD` • `Container Orchestration` • `Web Scraping` • `Parser Registry` • `Strategy Pattern` • `Prompt Engineering` • `Content Analysis` • `Database Engineering` • `Data Deduplication` • `Time-Series Analytics`
