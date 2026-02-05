import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles,
  Send,
  Bot,
  User,
  Lightbulb,
  Wand2,
  Calendar,
  CheckSquare,
  BarChart3,
  Zap,
  Clock,
  Copy,
  Check,
  Mic,
  Image as ImageIcon,
  Paperclip,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import DashboardLayout from '@/components/layout/DashboardLayout';

// Message types
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  suggestions?: string[];
  actions?: { label: string; action: string }[];
}

// Quick actions
const quickActions = [
  { icon: CheckSquare, label: 'Create Task', prompt: 'Create a new task for...' },
  { icon: Calendar, label: 'Schedule Meeting', prompt: 'Schedule a meeting with...' },
  { icon: BarChart3, label: 'View Analytics', prompt: 'Show me analytics for...' },
  { icon: Zap, label: 'Automate', prompt: 'Create an automation that...' },
];

// AI suggestions
const aiSuggestions = [
  'Summarize my tasks for today',
  'What are my top priorities?',
  'Create a sprint plan for next week',
  'Analyze team productivity trends',
  'Suggest tasks to delegate',
];

// Mock AI responses
const mockResponses: Record<string, string> = {
  'default': "I'd be happy to help you with that! Could you provide more details about what you'd like to accomplish?",
  'task': "I've created a task for you. Would you like me to assign it to someone or set a due date?",
  'schedule': "I can help you schedule that. What time works best for you and the participants?",
  'analytics': "Based on your recent data, your team's velocity has increased by 23% this week. Would you like to see a detailed breakdown?",
  'priority': "Here are your top priorities for today:\n\n1. Fix authentication bug (High Priority)\n2. Update API documentation (Medium Priority)\n3. Review pull requests (Medium Priority)",
};

// Typing indicator component
function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-2">
      <motion.div
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
        className="w-2 h-2 rounded-full bg-primary"
      />
      <motion.div
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
        className="w-2 h-2 rounded-full bg-primary"
      />
      <motion.div
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
        className="w-2 h-2 rounded-full bg-primary"
      />
    </div>
  );
}

// Message bubble component
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <Avatar className={`w-8 h-8 ${isUser ? 'bg-primary' : 'bg-primary/10'}`}>
        <AvatarFallback className={isUser ? 'text-primary-foreground' : 'text-primary'}>
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Content */}
      <div className={`flex-1 max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block text-left px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-primary text-primary-foreground rounded-br-sm'
              : 'bg-muted rounded-bl-sm'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Timestamp & Actions */}
        <div className={`flex items-center gap-2 mt-1 ${isUser ? 'justify-end' : ''}`}>
          <span className="text-xs text-muted-foreground">
            {message.timestamp.toLocaleTimeString('en-US', { 
              hour: 'numeric', 
              minute: '2-digit' 
            })}
          </span>
          {!isUser && (
            <button
              onClick={handleCopy}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            </button>
          )}
        </div>

        {/* Suggestions */}
        {message.suggestions && (
          <div className="flex flex-wrap gap-2 mt-3">
            {message.suggestions.map((suggestion, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="cursor-pointer hover:bg-primary/20 transition-colors"
              >
                <Lightbulb className="w-3 h-3 mr-1" />
                {suggestion}
              </Badge>
            ))}
          </div>
        )}

        {/* Actions */}
        {message.actions && (
          <div className="flex flex-wrap gap-2 mt-3">
            {message.actions.map((action, index) => (
              <Button key={index} size="sm" variant="outline">
                {action.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function AICommandCenter() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI assistant. I can help you manage tasks, analyze data, automate workflows, and much more. What would you like to do today?",
      timestamp: new Date(),
      suggestions: aiSuggestions.slice(0, 3),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const lowerInput = inputValue.toLowerCase();
      let responseContent = mockResponses.default;
      let suggestions: string[] = [];
      let actions: { label: string; action: string }[] = [];

      if (lowerInput.includes('task') || lowerInput.includes('create')) {
        responseContent = mockResponses.task;
        actions = [
          { label: 'Assign to me', action: 'assign' },
          { label: 'Set due date', action: 'duedate' },
        ];
      } else if (lowerInput.includes('schedule') || lowerInput.includes('meeting')) {
        responseContent = mockResponses.schedule;
      } else if (lowerInput.includes('analytics') || lowerInput.includes('data')) {
        responseContent = mockResponses.analytics;
        actions = [
          { label: 'View detailed report', action: 'report' },
        ];
      } else if (lowerInput.includes('priority') || lowerInput.includes('today')) {
        responseContent = mockResponses.priority;
        suggestions = ['Create tasks from priorities', 'Share with team'];
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseContent,
        timestamp: new Date(),
        suggestions,
        actions,
      };

      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickAction = (prompt: string) => {
    setInputValue(prompt);
  };

  const handleSuggestion = (suggestion: string) => {
    setInputValue(suggestion);
  };

  return (
    <DashboardLayout>
      <div className="h-[calc(100vh-8rem)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent-primary flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">AI Command Center</h1>
              <p className="text-sm text-muted-foreground">Powered by TaskPulse AI</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="gap-1">
              <Sparkles className="w-3 h-3" />
              GPT-4
            </Badge>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex gap-6 min-h-0">
          {/* Chat */}
          <Card className="flex-1 flex flex-col">
            {/* Messages */}
            <ScrollArea ref={scrollRef} className="flex-1 p-4">
              <div className="space-y-6">
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
                {isTyping && (
                  <div className="flex gap-4">
                    <Avatar className="w-8 h-8 bg-primary/10">
                      <AvatarFallback className="text-primary">
                        <Bot className="w-4 h-4" />
                      </AvatarFallback>
                    </Avatar>
                    <TypingIndicator />
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="p-4 border-t border-border/50">
              {/* Quick Actions */}
              <div className="flex gap-2 mb-3 overflow-x-auto pb-2">
                {quickActions.map((action, index) => {
                  const Icon = action.icon;
                  return (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      className="gap-2 flex-shrink-0"
                      onClick={() => handleQuickAction(action.prompt)}
                    >
                      <Icon className="w-4 h-4" />
                      {action.label}
                    </Button>
                  );
                })}
              </div>

              {/* Input */}
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Input
                    placeholder="Ask me anything..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="pr-24"
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Paperclip className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <ImageIcon className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Mic className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <Button onClick={handleSend} disabled={!inputValue.trim() || isTyping}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>

          {/* Sidebar */}
          <div className="hidden xl:block w-80 space-y-4">
            {/* AI Capabilities */}
            <Card>
              <CardContent className="p-4">
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <Wand2 className="w-4 h-4 text-primary" />
                  AI Capabilities
                </h3>
                <div className="space-y-2">
                  {[
                    { icon: CheckSquare, label: 'Create & manage tasks' },
                    { icon: Calendar, label: 'Schedule & plan' },
                    { icon: BarChart3, label: 'Analyze & report' },
                    { icon: Zap, label: 'Build automations' },
                    { icon: Clock, label: 'Time tracking' },
                  ].map((cap, index) => {
                    const Icon = cap.icon;
                    return (
                      <div key={index} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Icon className="w-4 h-4" />
                        {cap.label}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Suggestions */}
            <Card>
              <CardContent className="p-4">
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-amber-500" />
                  Try Asking
                </h3>
                <div className="space-y-2">
                  {aiSuggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestion(suggestion)}
                      className="w-full text-left text-sm text-muted-foreground hover:text-foreground hover:bg-muted p-2 rounded-lg transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardContent className="p-4">
                <h3 className="font-medium mb-3">Recent AI Actions</h3>
                <div className="space-y-3">
                  {[
                    { action: 'Created 3 tasks', time: '2 min ago' },
                    { action: 'Generated weekly report', time: '1 hour ago' },
                    { action: 'Scheduled team meeting', time: '3 hours ago' },
                  ].map((item, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">{item.action}</span>
                      <span className="text-xs text-muted-foreground">{item.time}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
