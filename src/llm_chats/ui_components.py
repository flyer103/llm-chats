"""Professional UI components for LLM Chats application."""
import gradio as gr
from typing import Dict, Any, List, Tuple, Optional


class ProfessionalTheme:
    """Professional theme configuration for the application."""
    
    @staticmethod
    def get_css() -> str:
        """Get professional CSS styling with dark mode and readable fonts."""
        return """
        /* Google Fonts Import */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Professional Dark Theme CSS */
        :root {
            /* Primary Colors - Optimized for dark mode */
            --primary-color: #60a5fa;
            --primary-light: #93c5fd;
            --primary-dark: #3b82f6;
            --secondary-color: #8b949e;
            --success-color: #22c55e;
            --warning-color: #fbbf24;
            --error-color: #f87171;
            
            /* Dark Mode Background Colors */
            --background-color: #0d1117;
            --surface-color: #161b22;
            --surface-hover: #21262d;
            --surface-active: #30363d;
            --border-color: #30363d;
            --border-hover: #484f58;
            
            /* Text Colors - Optimized for readability */
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --text-muted: #7d8590;
            --text-accent: #79c0ff;
            --text-link: #58a6ff;
            
            /* Shadows for dark mode */
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.4);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.5), 0 4px 6px -4px rgb(0 0 0 / 0.5);
            
            /* Border Radius */
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
            
            /* Gradients - Dark mode harmonized */
            --gradient-primary: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            --gradient-secondary: linear-gradient(135deg, #8b949e 0%, #6b7280 100%);
            --gradient-surface: linear-gradient(135deg, #161b22 0%, #21262d 100%);
            --gradient-header: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            
            /* Accent Colors */
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-purple: #a5a5ff;
            --accent-orange: #ffa657;
            --accent-red: #f85149;
        }
        
        /* Global styles with readable fonts */
        .gradio-container {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            background-color: var(--background-color);
            color: var(--text-primary);
            line-height: 1.7;
            font-size: 14px;
            font-weight: 400;
            letter-spacing: 0.01em;
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        /* Header styles - Compact & Dark mode harmonized */
        .app-header {
            background: var(--gradient-header);
            color: var(--text-primary);
            padding: 1.25rem 1rem;
            text-align: center;
            margin-bottom: 1.5rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
        }
        
        .app-title {
            font-size: 1.75rem;
            font-weight: 600;
            margin: 0;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
            color: var(--text-primary);
        }
        
        .app-subtitle {
            font-size: 0.95rem;
            margin-top: 0.375rem;
            opacity: 0.8;
            color: var(--text-secondary);
        }
        
        /* Card styles */
        .card {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
        }
        
        .card:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-1px);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0;
        }
        
        .card-icon {
            font-size: 1.5rem;
            color: var(--primary-color);
        }
        
        /* Button styles - Dark mode optimized */
        .btn-primary {
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            border: none;
            color: #ffffff;
            padding: 0.875rem 1.5rem;
            border-radius: var(--radius-md);
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: var(--shadow-sm);
            font-size: 0.9rem;
            cursor: pointer;
            letter-spacing: 0.025em;
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
            filter: brightness(1.1);
        }
        
        .btn-secondary {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.875rem 1.5rem;
            border-radius: var(--radius-md);
            font-weight: 500;
            transition: all 0.2s ease;
            font-size: 0.9rem;
            cursor: pointer;
            letter-spacing: 0.025em;
        }
        
        .btn-secondary:hover {
            background: var(--surface-hover);
            color: var(--text-primary);
            border-color: var(--primary-color);
            transform: translateY(-1px);
            box-shadow: var(--shadow-sm);
        }
        
        /* Status indicators - Dark mode optimized */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.875rem;
            border-radius: var(--radius-sm);
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.025em;
        }
        
        .status-success {
            background: rgba(34, 197, 94, 0.15);
            color: var(--success-color);
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        
        .status-warning {
            background: rgba(251, 191, 36, 0.15);
            color: var(--warning-color);
            border: 1px solid rgba(251, 191, 36, 0.3);
        }
        
        .status-error {
            background: rgba(248, 113, 113, 0.15);
            color: var(--error-color);
            border: 1px solid rgba(248, 113, 113, 0.3);
        }
        
        .status-info {
            background: rgba(96, 165, 250, 0.15);
            color: var(--primary-color);
            border: 1px solid rgba(96, 165, 250, 0.3);
        }
        
        /* Progress indicators */
        .progress-container {
            background: var(--surface-color);
            border-radius: var(--radius-md);
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--border-color);
            border-radius: var(--radius-sm);
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            transition: width 0.3s ease;
        }
        
        /* Compact progress display */
        .compact-progress {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 0.5rem 0.75rem;
            margin: 0 0 1rem 0;
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.4;
            min-height: auto !important;
        }
        
        .compact-progress p {
            margin: 0 !important;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        /* Conversation display - Dark mode optimized */
        .conversation-container {
            background: var(--surface-color);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
        }
        
        /* Compact conversation display */
        .conversation-display {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1rem;
            margin: 0;
            box-shadow: var(--shadow-sm);
            max-height: 60vh;
            overflow-y: auto;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        /* Fixed header for discussion topic, participants, and status */
        .fixed-header {
            position: sticky;
            top: 0;
            z-index: 100;
            background: var(--background-color);
            border-bottom: 1px solid var(--border-color);
            padding: 0.75rem;
            margin: -1rem -1rem 1rem -1rem;
            border-radius: var(--radius-md) var(--radius-md) 0 0;
            backdrop-filter: blur(10px);
            background: rgba(13, 17, 23, 0.95);
        }
        
        .fixed-header-content {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .fixed-header .discussion-topic-quote {
            margin: 0;
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
            border-radius: var(--radius-sm);
            background: var(--surface-hover);
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--primary-color);
        }
        
        .fixed-header .discussion-topic-quote::before {
            top: 0.5rem;
            left: -10px;
            width: 20px;
            height: 20px;
            font-size: 0.7rem;
        }
        
        .fixed-header .discussion-topic-quote .topic-label {
            font-size: 0.7rem;
            margin-bottom: 0.25rem;
        }
        
        .fixed-header .discussion-topic-quote .topic-content {
            font-size: 0.85rem;
            line-height: 1.4;
        }
        
        .fixed-header .discussion-participants {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin: 0;
            padding: 0.25rem 0;
            border-bottom: none;
        }
        
        .fixed-header .discussion-metadata {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin: 0;
        }
        
        /* Conversation content area - adjusted for fixed header */
        .conversation-content {
            position: relative;
            padding-top: 0.5rem;
        }
        
        .conversation-display {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1rem;
            margin: 0;
            box-shadow: var(--shadow-sm);
            max-height: 60vh;
            overflow-y: auto;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        .conversation-display h2 {
            font-size: 1.1rem;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .conversation-display h3 {
            font-size: 1rem;
            margin-top: 0.75rem;
            margin-bottom: 0.5rem;
        }
        
        .conversation-display h4 {
            font-size: 0.9rem;
            margin-top: 0.5rem;
            margin-bottom: 0.25rem;
        }
        
        .conversation-display p {
            margin-bottom: 0.75rem;
        }
        
        .conversation-round {
            border-left: 4px solid var(--primary-color);
            padding-left: 1rem;
            margin: 1.5rem 0;
            background: var(--surface-hover);
            border-radius: var(--radius-md);
            padding: 1rem;
        }
        
        .conversation-message {
            background: var(--surface-active);
            border-radius: var(--radius-md);
            padding: 1rem;
            margin: 0.75rem 0;
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
        }
        
        .conversation-message:hover {
            background: var(--surface-hover);
            border-color: var(--border-hover);
        }
        
        .message-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 0.9rem;
        }
        
        .platform-badge {
            padding: 0.3rem 0.6rem;
            border-radius: var(--radius-sm);
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .platform-alibaba { background: #ff6b35; color: #ffffff; }
        .platform-doubao { background: #ff4757; color: #ffffff; }
        .platform-moonshot { background: #3742fa; color: #ffffff; }
        .platform-deepseek { background: #2ed573; color: #000000; }
        .platform-ollama { background: #5352ed; color: #ffffff; }
        
        /* Reference links - Dark mode optimized */
        .references-container {
            background: rgba(96, 165, 250, 0.1);
            border-left: 4px solid var(--primary-color);
            padding: 1rem;
            margin: 1rem 0;
            border-radius: var(--radius-md);
            border: 1px solid rgba(96, 165, 250, 0.2);
        }
        
        .references-title {
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 0.75rem;
            font-size: 0.9rem;
        }
        
        .reference-link {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0;
            color: var(--text-link);
            text-decoration: none;
            transition: all 0.2s ease;
            font-size: 0.85rem;
            border-radius: var(--radius-sm);
            padding: 0.5rem;
            margin: 0.25rem 0;
        }
        
        .reference-link:hover {
            color: var(--primary-light);
            background: rgba(96, 165, 250, 0.1);
            transform: translateX(2px);
        }
        
        /* Streaming animation - Dark mode optimized */
        .streaming-content {
            position: relative;
            background: rgba(96, 165, 250, 0.1);
            border-radius: var(--radius-md);
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid var(--primary-color);
            border: 1px solid rgba(96, 165, 250, 0.2);
        }
        
        .streaming-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--primary-color);
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        /* Typography enhancements */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary);
            line-height: 1.4;
            margin-bottom: 1rem;
        }
        
        h1 { font-size: 2rem; font-weight: 700; }
        h2 { font-size: 1.5rem; font-weight: 600; }
        h3 { font-size: 1.25rem; font-weight: 600; }
        h4 { font-size: 1.125rem; font-weight: 600; }
        h5 { font-size: 1rem; font-weight: 600; }
        h6 { font-size: 0.875rem; font-weight: 600; }
        
        /* Discussion topic styling - Modern quote style */
        .discussion-topic-quote {
            background: var(--surface-color);
            border-left: 4px solid var(--primary-color);
            border-radius: var(--radius-md);
            padding: 1rem 1.25rem;
            margin: 0.75rem 0 1.5rem 0;
            font-size: 1rem;
            font-weight: 500;
            color: var(--text-primary);
            line-height: 1.5;
            box-shadow: var(--shadow-sm);
            position: relative;
            background: linear-gradient(135deg, var(--surface-color) 0%, var(--surface-hover) 100%);
            border: 1px solid var(--border-color);
        }
        
        .discussion-topic-quote::before {
            content: '💬';
            position: absolute;
            top: 0.75rem;
            left: -12px;
            background: var(--primary-color);
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            box-shadow: var(--shadow-sm);
        }
        
        .discussion-topic-quote .topic-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--primary-color);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
            display: block;
        }
        
        .discussion-topic-quote .topic-content {
            font-size: 0.95rem;
            color: var(--text-primary);
            line-height: 1.6;
            margin: 0;
        }
        
        .discussion-participants {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin: 0.75rem 0;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border-color);
            display: block;
        }
        
        .discussion-metadata {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 1rem;
        }
        
        p {
            color: var(--text-primary);
            line-height: 1.7;
            margin-bottom: 1rem;
        }
        
        a {
            color: var(--text-link);
            text-decoration: underline;
            transition: color 0.2s ease;
        }
        
        a:hover {
            color: var(--primary-light);
        }
        
        /* Form styles - Dark mode optimized */
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            display: block;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }
        
        .form-input {
            width: 100%;
            padding: 0.875rem;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            background: var(--surface-color);
            color: var(--text-primary);
            transition: all 0.2s ease;
            font-size: 0.9rem;
            font-family: inherit;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
            background: var(--surface-hover);
        }
        
        .form-input::placeholder {
            color: var(--text-muted);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .app-header {
                padding: 1rem 0.75rem;
                margin-bottom: 1rem;
            }
            
            .app-title {
                font-size: 1.5rem;
            }
            
            .app-subtitle {
                font-size: 0.875rem;
            }
            
            /* Mobile optimization for discussion topic */
            .discussion-topic-quote {
                padding: 0.875rem 1rem;
                margin: 0.5rem 0 1rem 0;
                font-size: 0.9rem;
            }
            
            .discussion-topic-quote::before {
                width: 20px;
                height: 20px;
                font-size: 0.7rem;
                top: 0.6rem;
                left: -10px;
            }
            
            .discussion-topic-quote .topic-label {
                font-size: 0.7rem;
                margin-bottom: 0.375rem;
            }
            
            .discussion-topic-quote .topic-content {
                font-size: 0.875rem;
                line-height: 1.5;
            }
            
            .discussion-participants {
                font-size: 0.85rem;
                padding: 0.375rem 0;
            }
            
            .discussion-metadata {
                font-size: 0.8rem;
            }
            
            /* Mobile optimization for compact UI */
            .compact-progress {
                padding: 0.375rem 0.5rem;
                font-size: 0.75rem;
                margin: 0 0 0.75rem 0;
            }
            
            .conversation-display {
                padding: 0.75rem;
                font-size: 0.85rem;
                max-height: 50vh;
            }
            
            .conversation-display h2 {
                font-size: 1rem;
                margin-top: 0.75rem;
                margin-bottom: 0.375rem;
            }
            
            .conversation-display h3 {
                font-size: 0.9rem;
                margin-top: 0.5rem;
                margin-bottom: 0.375rem;
            }
            
            .conversation-display h4 {
                font-size: 0.85rem;
                margin-top: 0.375rem;
                margin-bottom: 0.25rem;
            }
            
            /* Mobile optimization for fixed header */
            .fixed-header {
                padding: 0.5rem;
                margin: -0.75rem -0.75rem 0.75rem -0.75rem;
            }
            
            .fixed-header .discussion-topic-quote {
                padding: 0.5rem 0.75rem;
                font-size: 0.8rem;
            }
            
            .fixed-header .discussion-topic-quote::before {
                width: 18px;
                height: 18px;
                font-size: 0.6rem;
                top: 0.4rem;
                left: -9px;
            }
            
            .fixed-header .discussion-topic-quote .topic-label {
                font-size: 0.65rem;
                margin-bottom: 0.2rem;
            }
            
            .fixed-header .discussion-topic-quote .topic-content {
                font-size: 0.8rem;
                line-height: 1.3;
            }
            
            .fixed-header .discussion-participants {
                font-size: 0.75rem;
                padding: 0.2rem 0;
            }
            
            .fixed-header .discussion-metadata {
                font-size: 0.7rem;
            }
            
            .fixed-header-content {
                gap: 0.375rem;
            }
            
            .card {
                padding: 1rem;
            }
            
            .btn-primary,
            .btn-secondary {
                padding: 0.5rem 1rem;
            }
        }
        
        /* Accessibility enhancements */
        *:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--surface-color);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: var(--radius-sm);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--border-hover);
        }
        """
    
    @staticmethod
    def get_js() -> str:
        """Get JavaScript for enhanced interactions."""
        return """
        function initializeProfessionalUI() {
            // Add smooth scrolling
            document.documentElement.style.scrollBehavior = 'smooth';
            
            // Add loading states to buttons
            const buttons = document.querySelectorAll('button');
            buttons.forEach(button => {
                button.addEventListener('click', function() {
                    if (!this.disabled) {
                        this.classList.add('loading');
                        setTimeout(() => {
                            this.classList.remove('loading');
                        }, 1000);
                    }
                });
            });
            
            // Add tooltips
            const tooltipElements = document.querySelectorAll('[data-tooltip]');
            tooltipElements.forEach(element => {
                element.addEventListener('mouseenter', function() {
                    const tooltip = document.createElement('div');
                    tooltip.className = 'tooltip';
                    tooltip.textContent = this.getAttribute('data-tooltip');
                    document.body.appendChild(tooltip);
                    
                    const rect = this.getBoundingClientRect();
                    tooltip.style.left = rect.left + 'px';
                    tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
                });
                
                element.addEventListener('mouseleave', function() {
                    const tooltip = document.querySelector('.tooltip');
                    if (tooltip) {
                        tooltip.remove();
                    }
                });
            });
            
            // Add keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey || e.metaKey) {
                    switch(e.key) {
                        case 'Enter':
                            e.preventDefault();
                            const startBtn = document.querySelector('[data-action="start"]');
                            if (startBtn && !startBtn.disabled) {
                                startBtn.click();
                            }
                            break;
                        case 's':
                            e.preventDefault();
                            const summaryBtn = document.querySelector('[data-action="summary"]');
                            if (summaryBtn && !summaryBtn.disabled) {
                                summaryBtn.click();
                            }
                            break;
                    }
                }
            });
            
            // Add auto-save functionality
            const inputs = document.querySelectorAll('input, textarea');
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    localStorage.setItem('llm_chats_' + this.name, this.value);
                });
                
                // Restore saved values
                const savedValue = localStorage.getItem('llm_chats_' + input.name);
                if (savedValue) {
                    input.value = savedValue;
                }
            });
            
            // Add progress tracking
            window.updateProgress = function(current, total) {
                const progressBar = document.querySelector('.progress-fill');
                if (progressBar) {
                    const percentage = (current / total) * 100;
                    progressBar.style.width = percentage + '%';
                }
            };
            
            // Add notification system
            window.showNotification = function(message, type = 'info') {
                const notification = document.createElement('div');
                notification.className = `notification notification-${type}`;
                notification.textContent = message;
                
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.classList.add('show');
                }, 100);
                
                setTimeout(() => {
                    notification.classList.remove('show');
                    setTimeout(() => {
                        notification.remove();
                    }, 300);
                }, 3000);
            };
        }
        
        // Initialize when DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeProfessionalUI);
        } else {
            initializeProfessionalUI();
        }
        """


class ConversationCard:
    """Professional conversation display card."""
    
    @staticmethod
    def create_conversation_display() -> gr.Markdown:
        """Create a professional conversation display component."""
        return gr.Markdown(
            value="",
            elem_classes=["conversation-container"],
            elem_id="conversation-display"
        )
    
    @staticmethod
    def create_progress_display() -> gr.Markdown:
        """Create a professional progress display component."""
        return gr.Markdown(
            value="<div class='progress-container'><div class='progress-bar'><div class='progress-fill' style='width: 0%'></div></div><p>等待开始讨论...</p></div>",
            elem_classes=["progress-container"],
            elem_id="progress-display"
        )


class StatusIndicator:
    """Professional status indicator component."""
    
    @staticmethod
    def create_status_display(label: str, initial_value: str = "准备中...") -> gr.Markdown:
        """Create a professional status indicator."""
        return gr.Markdown(
            value=f"<div class='status-indicator'>{initial_value}</div>",
            elem_classes=["status-display"],
            label=label
        )
    
    @staticmethod
    def format_status(message: str, status_type: str = "info") -> str:
        """Format status message with appropriate styling."""
        emoji_map = {
            "success": "✅",
            "warning": "⚠️", 
            "error": "❌",
            "info": "ℹ️",
            "loading": "⏳"
        }
        
        emoji = emoji_map.get(status_type, "ℹ️")
        css_class = f"status-{status_type}"
        
        return f"<div class='status-indicator {css_class}'>{emoji} {message}</div>"


class ProfessionalLayout:
    """Professional layout components."""
    
    @staticmethod
    def create_header() -> gr.Markdown:
        """Create application header."""
        return gr.Markdown(
            """
            <div class="app-header">
                <h1 class="app-title">🤖 LLM Chats</h1>
                <p class="app-subtitle">多模型协作深度研究平台</p>
            </div>
            """,
            elem_classes=["app-header"]
        )
    
    @staticmethod
    def create_card_container(title: str, icon: str = "🔧") -> gr.Group:
        """Create a professional card container."""
        return gr.Group(elem_classes=["card"])
    
    @staticmethod
    def create_card_header(title: str, icon: str = "🔧") -> gr.Markdown:
        """Create a professional card header."""
        return gr.Markdown(
            f"""
            <div class="card-header">
                <span class="card-icon">{icon}</span>
                <h3 class="card-title">{title}</h3>
            </div>
            """,
            elem_classes=["card-header"]
        ) 