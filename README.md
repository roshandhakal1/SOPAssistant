# 🏭 SOP Assistant - Manufacturing Intelligence Hub

An advanced AI-powered platform that combines Standard Operating Procedure (SOP) knowledge with expert manufacturing consultation. Built with secure authentication and modern UI design.

## ✨ Features

### 🔐 Secure Authentication
- **Multi-user support** with role-based access (Admin/User)
- **Session management** with 4-hour timeout
- **Secure password hashing** with SHA-256
- **Environment-based credentials** for production security

### 🎯 Dual Operation Modes
- **Knowledge Search**: Quick SOP lookups with smart abbreviation expansion
- **Expert Consultant**: In-depth manufacturing expertise combining CEO, CFO, CMO, Quality Director, and Supply Chain Director perspectives

### 📚 Advanced Document Processing
- **Multi-format support**: PDF, DOCX, DOC files
- **Intelligent chunking** with overlap for context retention
- **Session uploads**: Temporary document processing for enhanced context
- **Automatic updates** with file change detection

### 🔍 Smart Search Capabilities
- **Abbreviation mapping**: 80+ business/manufacturing abbreviations (AP→Accounts Payable)
- **Semantic search** using Google Gemini embeddings
- **Vector storage** with ChromaDB for fast retrieval
- **Source attribution** with clear document references

### 💬 Modern Chat Interface
- **Apple-inspired design** with professional typography
- **Floating expert indicator** with smooth animations
- **Chat management**: Clear, new chat, export functionality
- **Session history** with conversation persistence

### 🚀 Cloud-Ready Deployment
- **Streamlit Cloud** compatible with secrets management
- **Docker support** for containerized deployment
- **Environment configuration** for multiple platforms
- **Production security** with configurable authentication

## 🚀 Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/roshandhakal1/gemini.git
cd gemini

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-gemini-api-key"
export SOP_FOLDER="/path/to/your/sops"

# Run application
streamlit run app.py
```

### Cloud Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed cloud deployment instructions.

**Quick Streamlit Cloud Deploy:**
1. Fork this repository
2. Connect to [share.streamlit.io](https://share.streamlit.io)
3. Add secrets in Streamlit Cloud dashboard
4. Deploy with one click!

## 🔑 Default Credentials
```
Admin: admin / admin123
User: user / user123
```
**⚠️ Change these in production!**

## 🏗️ Architecture

```
├── app.py                      # Main Streamlit application
├── auth.py                     # Authentication & session management
├── expert_consultant.py       # Manufacturing expertise engine
├── abbreviation_mapper.py     # Smart query expansion
├── session_document_handler.py # Temporary document processing
├── prompt_templates.py        # Expert consultation prompts
├── rag_handler.py             # Enhanced RAG with abbreviations
├── vector_db.py               # ChromaDB with unique counting
├── document_processor.py      # Multi-format document processing
├── embeddings_manager.py      # Google Gemini embeddings
├── config.py                  # Configuration management
├── .streamlit/
│   ├── config.toml            # Streamlit configuration
│   └── secrets.toml.example   # Secrets template
├── DEPLOYMENT.md              # Deployment guide
└── requirements.txt           # Dependencies
```

## 🎨 UI Features

- **Large SOP Assistant branding** with professional typography
- **Condensed document management** in expandable sections
- **Mode-aware interface** with dynamic content
- **Expert floating indicator** with smooth animations
- **Clean header design** without anchor artifacts
- **Responsive layout** optimized for desktop use

## 🔧 Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Authentication (change in production!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password
USER_USERNAME=user  
USER_PASSWORD=your_secure_user_password

# Optional
SOP_FOLDER=/path/to/sops
CHROMA_PERSIST_DIR=./chroma_db
```

### Streamlit Secrets
```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "your_api_key"
ADMIN_PASSWORD = "secure_password"
# ... other secrets
```

## 🚀 Expert Consultant Capabilities

### Multi-Role Expertise
- **CEO**: Strategic planning, innovation, market positioning
- **CFO**: Financial optimization, ROI analysis, cost management  
- **CMO**: Market trends, consumer insights, brand development
- **Quality Director**: GMP, HACCP, FDA compliance, certifications
- **Supply Chain**: Sourcing, logistics, inventory optimization

### Consultation Types
- Product Innovation & Development
- Production Optimization
- Quality & Compliance Management
- Supply Chain Enhancement
- Financial Analysis & Planning
- Strategic Business Planning

## 📊 Smart Features

### Abbreviation Expansion
- **Business Terms**: AP→Accounts Payable, ROI→Return on Investment
- **Manufacturing**: QC→Quality Control, GMP→Good Manufacturing Practice
- **Supply Chain**: SKU→Stock Keeping Unit, JIT→Just in Time
- **Quality**: HACCP→Hazard Analysis Critical Control Point

### Document Intelligence
- **Unique SOP counting** (not chunks)
- **Source attribution** with precise references
- **Session-based uploads** for temporary context
- **Multi-format processing** with robust error handling

## 🛡️ Security

- **Password hashing** with SHA-256
- **Session timeout** management
- **Environment-based secrets** 
- **Production-ready** authentication
- **No sensitive data** in repository

## 📈 Performance

- **Optimized mode switching** with cached components
- **Smooth animations** using CSS transitions
- **Efficient vector search** with ChromaDB
- **Smart chunking** for optimal context

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/roshandhakal1/gemini/issues)
- **Discussions**: [GitHub Discussions](https://github.com/roshandhakal1/gemini/discussions)
- **Documentation**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Built with ❤️ using Streamlit, Google Gemini AI, and modern web technologies**

🤖 *Enhanced with [Claude Code](https://claude.ai/code)*