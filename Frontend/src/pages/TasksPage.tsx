import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Search,
  Filter,
  MoreHorizontal,
  Calendar,
  List,
  LayoutGrid,
  Clock,
  GripVertical,
  ArrowUpDown,
  AlertTriangle,
  Loader2,
  Sparkles,
  Paperclip,
  MessageSquare,
  Bot,
  User,
  Send,
  CheckCircle2,
  Copy,
  Check,
  Lightbulb,
  Plus,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { TaskCreationSidebar } from '@/components/tasks/TaskCreationSidebar';
import { useUIStore } from '@/store/uiStore';
import { tasksService } from '@/services/tasks.service';
import { chatService } from '@/services/chat.service';
import { queryKeys } from '@/hooks/useApi';
import { mapTaskToFrontend, mapStatusToApi, type FrontendTask, type FrontendTaskStatus } from '@/types/mappers';
import { getApiErrorMessage } from '@/lib/api-client';
import { toast } from 'sonner';

// Priority config
const priorityConfig: Record<string, { color: string; label: string }> = {
  low: { color: 'bg-slate-500', label: 'Low' },
  medium: { color: 'bg-blue-500', label: 'Medium' },
  high: { color: 'bg-orange-500', label: 'High' },
  urgent: { color: 'bg-red-500', label: 'Urgent' },
};

// Status columns for Kanban
const columns = [
  { id: 'todo' as const, title: 'To Do', color: 'bg-slate-500' },
  { id: 'in-progress' as const, title: 'In Progress', color: 'bg-blue-500' },
  { id: 'review' as const, title: 'Review', color: 'bg-amber-500' },
  { id: 'done' as const, title: 'Done', color: 'bg-emerald-500' },
];

// ─── Chat message type ───────────────────────────────────────────────
interface ChatMsg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  suggestions?: string[];
  timestamp: Date;
}

// ─── Create Task Chat Dialog (inline AI) ─────────────────────────────
function DescribeTaskDialog({
  children,
  onTaskCreated,
}: {
  children: React.ReactNode;
  onTaskCreated?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [chatStarted, setChatStarted] = useState(false);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [taskCreated, setTaskCreated] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const resetDialog = () => {
    setDescription('');
    setFile(null);
    setChatStarted(false);
    setMessages([]);
    setInputValue('');
    setIsTyping(false);
    setConversationId(null);
    setTaskCreated(false);
  };

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
    if (!newOpen) resetDialog();
  };

  const addUserMessage = (text: string): ChatMsg => {
    const msg: ChatMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, msg]);
    return msg;
  };

  const addAssistantMessage = (content: string, suggestions?: string[]) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content,
        suggestions,
        timestamp: new Date(),
      },
    ]);
  };

  const sendToAI = async (message: string, fileToSend?: File) => {
    setIsTyping(true);
    try {
      let response;
      if (fileToSend) {
        response = await chatService.sendMessageWithFile(
          fileToSend,
          message || 'Please analyze this file and help me create a task from it.',
          conversationId ?? undefined,
        );
      } else {
        response = await chatService.sendMessage({
          message,
          conversation_id: conversationId ?? undefined,
        });
      }

      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      // Check if a task was created (AI response contains task creation confirmation)
      const content = response.message.content;
      if (
        content.toLowerCase().includes('task has been created') ||
        content.toLowerCase().includes('task created') ||
        content.toLowerCase().includes('successfully created')
      ) {
        setTaskCreated(true);
        onTaskCreated?.();
      }

      addAssistantMessage(content, response.suggestions);
    } catch (error) {
      addAssistantMessage(
        'Sorry, something went wrong. Please try again.',
      );
      toast.error(getApiErrorMessage(error));
    } finally {
      setIsTyping(false);
    }
  };

  // Initial submit (from the description form)
  const handleStart = async () => {
    if (!description.trim() && !file) return;
    setChatStarted(true);

    const text = description.trim() || `[Uploaded file: ${file!.name}]`;
    addUserMessage(text);
    setDescription('');

    await sendToAI(
      description.trim() || 'Please analyze this file and help me create a task from it.',
      file ?? undefined,
    );
    setFile(null);
  };

  // Follow-up messages in chat
  const handleSendMessage = async () => {
    const text = inputValue.trim();
    if (!text || isTyping) return;
    addUserMessage(text);
    setInputValue('');
    await sendToAI(text);
  };

  // Click a suggestion badge
  const handleSuggestionClick = async (suggestion: string) => {
    if (isTyping) return;
    addUserMessage(suggestion);
    await sendToAI(suggestion);
  };

  // File upload in chat
  const handleChatFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    addUserMessage(`[Uploaded file: ${f.name}]`);
    await sendToAI('', f);
    e.target.value = '';
  };

  const handleCopy = (text: string, msgId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] flex flex-col p-0 gap-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            {taskCreated ? 'Task Created!' : 'Describe Your Task'}
          </DialogTitle>
          <DialogDescription className="sr-only">Use AI to create a new task by describing what you need done.</DialogDescription>
        </DialogHeader>

        {!chatStarted ? (
          /* ─── Initial Input Form ─── */
          <div className="p-6 space-y-4">
            <div className="space-y-2">
              <Label>Describe what you need to do</Label>
              <Textarea
                placeholder="e.g., I need to build a REST API for user authentication with JWT tokens, set up database models, write tests..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={5}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault();
                    handleStart();
                  }
                }}
              />
            </div>
            <div className="space-y-2">
              <Label>Or upload a task description</Label>
              <div className="border-2 border-dashed rounded-lg p-4 text-center hover:border-primary/50 transition-colors">
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="hidden"
                  id="task-file-upload"
                />
                <label htmlFor="task-file-upload" className="cursor-pointer">
                  {file ? (
                    <div className="flex items-center justify-center gap-2 text-sm text-primary">
                      <Paperclip className="w-4 h-4" />
                      {file.name}
                      <button
                        type="button"
                        className="text-muted-foreground hover:text-foreground text-xs ml-2"
                        onClick={(e) => { e.preventDefault(); setFile(null); }}
                      >
                        Remove
                      </button>
                    </div>
                  ) : (
                    <div className="text-muted-foreground text-sm">
                      <Paperclip className="w-5 h-5 mx-auto mb-1 opacity-50" />
                      Click to upload PDF, DOCX, or TXT
                    </div>
                  )}
                </label>
              </div>
            </div>
            <Button
              className="w-full gap-2"
              disabled={!description.trim() && !file}
              onClick={handleStart}
            >
              <Bot className="w-4 h-4" />
              Start AI Task Creation
            </Button>
            <p className="text-xs text-muted-foreground text-center">
              The AI will ask about deadlines, priorities, and create the task with subtasks.
            </p>
          </div>
        ) : (
          /* ─── Chat View ─── */
          <>
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto px-6 py-4 space-y-4 min-h-[300px] max-h-[50vh]"
            >
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex gap-2 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <Avatar className="w-7 h-7 shrink-0 mt-0.5">
                      <AvatarFallback className={`text-[10px] ${
                        msg.role === 'assistant'
                          ? 'bg-primary/10 text-primary'
                          : 'bg-muted text-muted-foreground'
                      }`}>
                        {msg.role === 'assistant' ? <Bot className="w-3.5 h-3.5" /> : <User className="w-3.5 h-3.5" />}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div
                        className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                          msg.role === 'user'
                            ? 'bg-primary text-primary-foreground rounded-br-md'
                            : 'bg-muted rounded-bl-md'
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>

                      {/* Copy button for AI messages */}
                      {msg.role === 'assistant' && (
                        <button
                          onClick={() => handleCopy(msg.content, msg.id)}
                          className="mt-1 text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {copiedId === msg.id ? (
                            <Check className="w-3 h-3 text-emerald-500" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      )}

                      {/* Suggestion badges */}
                      {msg.suggestions && msg.suggestions.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {msg.suggestions.map((s, i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="cursor-pointer hover:bg-primary/10 hover:border-primary/50 transition-colors text-xs"
                              onClick={() => handleSuggestionClick(s)}
                            >
                              <Lightbulb className="w-3 h-3 mr-1" />
                              {s}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex gap-2 max-w-[85%]">
                    <Avatar className="w-7 h-7 shrink-0 mt-0.5">
                      <AvatarFallback className="text-[10px] bg-primary/10 text-primary">
                        <Bot className="w-3.5 h-3.5" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="bg-muted rounded-2xl rounded-bl-md px-4 py-3">
                      <div className="flex gap-1.5">
                        <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:0ms]" />
                        <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:150ms]" />
                        <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:300ms]" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Task created success message */}
              {taskCreated && (
                <div className="flex justify-center">
                  <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 rounded-full px-4 py-2 text-sm">
                    <CheckCircle2 className="w-4 h-4" />
                    Task created successfully!
                  </div>
                </div>
              )}
            </div>

            {/* Chat input area */}
            <div className="border-t px-6 py-4 shrink-0">
              {taskCreated ? (
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1 gap-2"
                    onClick={resetDialog}
                  >
                    <Sparkles className="w-4 h-4" />
                    Create Another Task
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={() => handleOpenChange(false)}
                  >
                    Done
                  </Button>
                </div>
              ) : (
                <div className="flex items-end gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt,.md"
                    className="hidden"
                    onChange={handleChatFileUpload}
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0 text-muted-foreground hover:text-foreground"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isTyping}
                  >
                    <Paperclip className="w-4 h-4" />
                  </Button>
                  <Textarea
                    placeholder="Type your reply..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    rows={1}
                    className="min-h-[40px] max-h-[120px] resize-none"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                  />
                  <Button
                    size="icon"
                    className="shrink-0"
                    disabled={!inputValue.trim() || isTyping}
                    onClick={handleSendMessage}
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ─── Task Detail Panel (Sheet) ───────────────────────────────────────
function TaskDetailPanel({
  task,
  onClose,
}: {
  task: FrontendTask;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [blockerDesc, setBlockerDesc] = useState('');
  const [showBlockerForm, setShowBlockerForm] = useState(false);

  const { data: subtasks, isLoading: subtasksLoading } = useQuery({
    queryKey: queryKeys.tasks.subtasks(task.id),
    queryFn: () => tasksService.getSubtasks(task.id),
  });

  const { data: commentsData } = useQuery({
    queryKey: queryKeys.tasks.comments(task.id),
    queryFn: () => tasksService.getComments(task.id),
  });
  const comments = Array.isArray(commentsData) ? commentsData : (commentsData as any)?.comments ?? [];

  const blockerMutation = useMutation({
    mutationFn: () =>
      tasksService.updateStatus(task.id, {
        status: 'blocked',
        blocker_type: 'bug',
        blocker_description: blockerDesc,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      toast.success('Blocker reported — AI agent is analyzing...');
      setBlockerDesc('');
      setShowBlockerForm(false);
      chatService.sendMessage({
        message: `I'm blocked on task "${task.title}": ${blockerDesc}`,
      });
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const statusLabels: Record<string, string> = {
    'todo': 'To Do', 'in-progress': 'In Progress', 'review': 'Review', 'done': 'Done',
  };

  return (
    <Sheet open onOpenChange={() => onClose()}>
      <SheetContent side="right" className="sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{task.title}</SheetTitle>
        </SheetHeader>
        <div className="space-y-6 px-4 pb-6">
          {task.description && (
            <p className="text-sm text-muted-foreground">{task.description}</p>
          )}
          <div className="flex gap-2">
            <Badge variant="outline">{statusLabels[task.status] ?? task.status}</Badge>
            <Badge variant="secondary">{priorityConfig[task.priority]?.label ?? task.priority}</Badge>
            {task.dueDate && (
              <Badge variant="outline" className="text-xs">
                <Calendar className="w-3 h-3 mr-1" />
                {new Date(task.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </Badge>
            )}
          </div>

          {/* Subtasks */}
          <div>
            <h3 className="font-medium mb-2 text-sm">Subtasks</h3>
            {subtasksLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : subtasks && subtasks.length > 0 ? (
              <div className="space-y-2">
                {subtasks.map((sub: any) => (
                  <div
                    key={sub.id}
                    className="flex items-center justify-between p-3 rounded-lg border"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{sub.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-[10px]">
                          {sub.status?.replace('_', ' ')}
                        </Badge>
                        {sub.estimated_hours && (
                          <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                            <Clock className="w-2.5 h-2.5" />{sub.estimated_hours}h
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-amber-600 shrink-0"
                      onClick={() => setShowBlockerForm(true)}
                    >
                      Report Issue
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No subtasks yet.</p>
            )}
          </div>

          {/* Blocker Report Form */}
          {showBlockerForm && (
            <div className="space-y-3 border rounded-lg p-4 bg-amber-50 dark:bg-amber-500/5">
              <h3 className="font-medium text-sm text-amber-800 dark:text-amber-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Report a Blocker
              </h3>
              <Textarea
                placeholder="Describe what's blocking you... Include error messages if any."
                value={blockerDesc}
                onChange={(e) => setBlockerDesc(e.target.value)}
                rows={3}
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="gap-1"
                  disabled={!blockerDesc.trim() || blockerMutation.isPending}
                  onClick={() => blockerMutation.mutate()}
                >
                  {blockerMutation.isPending && <Loader2 className="w-3 h-3 animate-spin" />}
                  Report & Get AI Help
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setShowBlockerForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {!showBlockerForm && (
            <Button
              variant="outline"
              className="w-full gap-2 text-amber-600 border-amber-300 hover:bg-amber-50 dark:hover:bg-amber-500/5"
              onClick={() => setShowBlockerForm(true)}
            >
              <AlertTriangle className="w-4 h-4" />
              Report Blocker / Issue
            </Button>
          )}

          {/* Comments */}
          {comments.length > 0 && (
            <div>
              <h3 className="font-medium mb-2 text-sm flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                Comments
              </h3>
              <div className="space-y-2">
                {comments.map((comment: any) => (
                  <div key={comment.id} className="p-3 rounded-lg bg-muted text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-xs">
                        {comment.is_ai_generated ? (
                          <span className="flex items-center gap-1 text-primary">
                            <Bot className="w-3 h-3" /> AI Agent
                          </span>
                        ) : (
                          comment.user_name ?? 'User'
                        )}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {new Date(comment.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap text-xs">{comment.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

// ─── Kanban View ─────────────────────────────────────────────────────
function KanbanView({
  tasks, onStatusChange, onDelete, onSelect,
}: {
  tasks: FrontendTask[];
  onStatusChange: (id: string, status: FrontendTaskStatus) => void;
  onDelete: (id: string) => void;
  onSelect: (task: FrontendTask) => void;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {columns.map((column) => {
        const columnTasks = tasks.filter((task) => task.status === column.id);
        return (
          <div key={column.id} className="flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${column.color}`} />
                <span className="font-medium">{column.title}</span>
                <Badge variant="secondary" className="text-xs">{columnTasks.length}</Badge>
              </div>
            </div>
            <div className="space-y-3">
              <AnimatePresence>
                {columnTasks.map((task) => (
                  <motion.div
                    key={task.id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                  >
                    <TaskCard task={task} onStatusChange={onStatusChange} onDelete={onDelete} onSelect={onSelect} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Task Card ───────────────────────────────────────────────────────
function TaskCard({
  task, onStatusChange, onDelete, onSelect,
}: {
  task: FrontendTask;
  onStatusChange: (id: string, status: FrontendTaskStatus) => void;
  onDelete: (id: string) => void;
  onSelect: (task: FrontendTask) => void;
}) {
  const priority = priorityConfig[task.priority] ?? priorityConfig.medium;
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow group"
      onClick={() => onSelect(task)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className={`w-2 h-2 rounded-full ${priority.color} mt-1.5`} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {columns.filter((c) => c.id !== task.status).map((col) => (
                <DropdownMenuItem key={col.id} onClick={(e) => { e.stopPropagation(); onStatusChange(task.id, col.id); }}>
                  Move to {col.title}
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem className="text-destructive" onClick={(e) => { e.stopPropagation(); onDelete(task.id); }}>Delete</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <h4 className="font-medium mb-2 line-clamp-2">{task.title}</h4>
        {task.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {task.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
            ))}
          </div>
        )}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Avatar className="w-6 h-6">
              <AvatarFallback className="text-[10px] bg-primary/10 text-primary">
                {task.assigneeName ? task.assigneeName.charAt(0).toUpperCase() : <User className="w-3 h-3" />}
              </AvatarFallback>
            </Avatar>
            {task.estimatedHours > 0 && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {task.estimatedHours}h
              </span>
            )}
          </div>
          {task.dueDate && (
            <span className={`text-xs ${new Date(task.dueDate) < new Date() ? 'text-red-500' : 'text-muted-foreground'}`}>
              {new Date(task.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── List View ───────────────────────────────────────────────────────
function ListView({
  tasks, onStatusChange: _onStatusChange, onDelete: _onDelete, onSelect,
}: {
  tasks: FrontendTask[];
  onStatusChange: (id: string, status: FrontendTaskStatus) => void;
  onDelete: (id: string) => void;
  onSelect: (task: FrontendTask) => void;
}) {
  return (
    <Card>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border/50">
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <GripVertical className="w-4 h-4 opacity-0" />
                  Task
                </div>
              </th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Status</th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Priority</th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Assignee</th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Due Date</th>
              <th className="text-left p-4 font-medium text-sm text-muted-foreground">Est.</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => {
              const priority = priorityConfig[task.priority] ?? priorityConfig.medium;
              const statusLabels: Record<string, string> = {
                'todo': 'To Do', 'in-progress': 'In Progress', 'review': 'Review', 'done': 'Done',
              };
              return (
                <tr
                  key={task.id}
                  className="border-b border-border/50 hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => onSelect(task)}
                >
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <GripVertical className="w-4 h-4 text-muted-foreground cursor-grab" />
                      <div>
                        <p className="font-medium">{task.title}</p>
                        <div className="flex gap-1 mt-1">
                          {task.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4"><Badge variant="outline" className="text-xs">{statusLabels[task.status]}</Badge></td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${priority.color}`} />
                      <span className="text-sm">{priority.label}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="text-xs bg-primary/10 text-primary">
                        {task.assigneeName ? task.assigneeName.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
                      </AvatarFallback>
                    </Avatar>
                  </td>
                  <td className="p-4">
                    {task.dueDate ? (
                      <span className={`text-sm ${new Date(task.dueDate) < new Date() ? 'text-red-500' : ''}`}>
                        {new Date(task.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                    ) : (
                      <span className="text-sm text-muted-foreground">-</span>
                    )}
                  </td>
                  <td className="p-4"><span className="text-sm text-muted-foreground">{task.estimatedHours > 0 ? `${task.estimatedHours}h` : '-'}</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ─── Timeline View ───────────────────────────────────────────────────
function TimelineView({ tasks }: { tasks: FrontendTask[] }) {
  const sortedTasks = [...tasks].filter((t) => t.dueDate).sort((a, b) =>
    new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime()
  );
  const groupedByDate = sortedTasks.reduce((acc, task) => {
    const date = task.dueDate.split('T')[0];
    if (!acc[date]) acc[date] = [];
    acc[date].push(task);
    return acc;
  }, {} as Record<string, FrontendTask[]>);

  if (Object.keys(groupedByDate).length === 0) {
    return <p className="text-center text-muted-foreground py-12">No tasks with due dates to display in timeline view.</p>;
  }

  return (
    <div className="space-y-6">
      {Object.entries(groupedByDate).map(([date, dateTasks]) => (
        <div key={date} className="relative">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="font-medium">
                {new Date(date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </p>
              <p className="text-sm text-muted-foreground">{dateTasks.length} tasks</p>
            </div>
          </div>
          <div className="absolute left-5 top-14 bottom-0 w-px bg-border" />
          <div className="space-y-3 ml-12">
            {dateTasks.map((task) => (
              <Card key={task.id} className="p-4">
                <h4 className="font-medium">{task.title}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-[10px]">{task.priority}</Badge>
                  <span className="text-xs text-muted-foreground capitalize">{task.status.replace('-', ' ')}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main Tasks Page ─────────────────────────────────────────────────
export default function TasksPage() {
  const [view, setView] = useState<'kanban' | 'list' | 'timeline'>('kanban');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTask, setSelectedTask] = useState<FrontendTask | null>(null);
  const queryClient = useQueryClient();
  const { toggleTaskCreationSidebar } = useUIStore();

  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.tasks.list({ search: searchQuery || undefined, root_only: true, limit: 100 }),
    queryFn: () => tasksService.list({ search: searchQuery || undefined, root_only: true, limit: 100 }),
  });

  const tasks = (data?.tasks ?? []).map(mapTaskToFrontend);

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: FrontendTaskStatus }) =>
      tasksService.updateStatus(id, { status: mapStatusToApi(status) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all }),
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => tasksService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      toast.success('Task deleted');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const handleStatusChange = (id: string, status: FrontendTaskStatus) => statusMutation.mutate({ id, status });
  const handleDelete = (id: string) => deleteMutation.mutate(id);

  if (error) {
    return (
      <DashboardLayout>
        <Card className="p-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertTriangle className="w-12 h-12 text-amber-500" />
            <h2 className="text-lg font-semibold">Failed to load tasks</h2>
            <p className="text-muted-foreground">{(error as Error).message}</p>
            <Button onClick={() => queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })}>Retry</Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Tasks</h1>
            <p className="text-muted-foreground mt-1">Manage and track your tasks</p>
          </div>
          <div className="flex gap-2">
            <DescribeTaskDialog onTaskCreated={() => queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })}>
              <Button variant="outline" className="gap-2">
                <Sparkles className="w-4 h-4" />
                AI Describe
              </Button>
            </DescribeTaskDialog>
            <Button className="gap-2" onClick={toggleTaskCreationSidebar}>
              <Plus className="w-4 h-4" />
              Create Task
            </Button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search tasks..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="gap-2">
              <Filter className="w-4 h-4" />
              Filter
            </Button>
            <Button variant="outline" className="gap-2">
              <ArrowUpDown className="w-4 h-4" />
              Sort
            </Button>
            <Tabs value={view} onValueChange={(v) => setView(v as typeof view)}>
              <TabsList>
                <TabsTrigger value="kanban" className="gap-2">
                  <LayoutGrid className="w-4 h-4" />
                  <span className="hidden sm:inline">Board</span>
                </TabsTrigger>
                <TabsTrigger value="list" className="gap-2">
                  <List className="w-4 h-4" />
                  <span className="hidden sm:inline">List</span>
                </TabsTrigger>
                <TabsTrigger value="timeline" className="gap-2">
                  <Calendar className="w-4 h-4" />
                  <span className="hidden sm:inline">Timeline</span>
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-3">
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-32 w-full rounded-xl" />
                <Skeleton className="h-32 w-full rounded-xl" />
              </div>
            ))}
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={view}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {view === 'kanban' && <KanbanView tasks={tasks} onStatusChange={handleStatusChange} onDelete={handleDelete} onSelect={setSelectedTask} />}
              {view === 'list' && <ListView tasks={tasks} onStatusChange={handleStatusChange} onDelete={handleDelete} onSelect={setSelectedTask} />}
              {view === 'timeline' && <TimelineView tasks={tasks} />}
            </motion.div>
          </AnimatePresence>
        )}
      </div>

      {/* Task Detail Panel */}
      {selectedTask && (
        <TaskDetailPanel
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
        />
      )}

      {/* Task Creation Sidebar */}
      <TaskCreationSidebar />
    </DashboardLayout>
  );
}
