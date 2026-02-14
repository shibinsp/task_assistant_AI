import { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BookOpen,
  Upload,
  Search,
  Plus,
  FileText,
  Trash2,
  Edit3,
  Eye,
  X,
  Loader2,
  Database,
  Clock,
  Hash,
  CheckCircle2,
  AlertCircle,
  Filter,
  UploadCloud,
  File,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { aiService } from '@/services/ai.service';
import { queryKeys } from '@/hooks/useApi';
import { getApiErrorMessage } from '@/lib/api-client';
import type {
  ApiDocument,
  ApiDocumentCreate,
  ApiDocumentUpdate,
  ApiDocumentType,
} from '@/types/api';

// ─── Constants ──────────────────────────────────────────────────────

const DOC_TYPES: { value: ApiDocumentType; label: string }[] = [
  { value: 'guide', label: 'Guide' },
  { value: 'faq', label: 'FAQ' },
  { value: 'tutorial', label: 'Tutorial' },
  { value: 'reference', label: 'Reference' },
  { value: 'troubleshooting', label: 'Troubleshooting' },
  { value: 'other', label: 'Other' },
];

const DOC_TYPE_COLORS: Record<ApiDocumentType, string> = {
  guide: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  faq: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  tutorial: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  reference: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
  troubleshooting: 'bg-red-500/10 text-red-600 dark:text-red-400',
  other: 'bg-slate-500/10 text-slate-600 dark:text-slate-400',
};

const STATUS_CONFIG: Record<string, { color: string; icon: typeof CheckCircle2 }> = {
  indexed: { color: 'text-emerald-500', icon: CheckCircle2 },
  processing: { color: 'text-amber-500', icon: Loader2 },
  pending: { color: 'text-blue-500', icon: Clock },
  failed: { color: 'text-red-500', icon: AlertCircle },
  archived: { color: 'text-slate-500', icon: FileText },
};

// ─── Status Overview Card ───────────────────────────────────────────

function StatusOverview() {
  const { data: status, isLoading } = useQuery({
    queryKey: queryKeys.ai.knowledgeBase.status,
    queryFn: () => aiService.getKnowledgeBaseStatus(),
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-8 w-16" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!status) return null;

  const stats = [
    {
      label: 'Total Documents',
      value: status.total_documents,
      icon: FileText,
      color: 'text-primary',
    },
    {
      label: 'Indexed',
      value: status.indexed_documents,
      icon: CheckCircle2,
      color: 'text-emerald-500',
    },
    {
      label: 'Pending',
      value: status.pending_documents,
      icon: Clock,
      color: 'text-amber-500',
    },
    {
      label: 'Total Chunks',
      value: status.total_chunks,
      icon: Hash,
      color: 'text-blue-500',
    },
  ];

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-primary" />
            <h2 className="font-semibold">Knowledge Base Status</h2>
          </div>
          {status.failed_documents > 0 && (
            <Badge variant="destructive" className="gap-1">
              <AlertCircle className="w-3 h-3" />
              {status.failed_documents} failed
            </Badge>
          )}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label}>
                <div className="flex items-center gap-2 mb-1">
                  <Icon className={`w-4 h-4 ${stat.color}`} />
                  <span className="text-xs text-muted-foreground">{stat.label}</span>
                </div>
                <p className="text-2xl font-bold">{stat.value.toLocaleString()}</p>
              </div>
            );
          })}
        </div>
        {status.last_updated && (
          <p className="text-xs text-muted-foreground mt-4">
            Last updated: {new Date(status.last_updated).toLocaleString()}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Upload Zone ────────────────────────────────────────────────────

function UploadZone() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => aiService.uploadDocument(file),
    onSuccess: () => {
      toast.success('Document uploaded successfully');
      queryClient.invalidateQueries({ queryKey: queryKeys.ai.knowledgeBase.status });
      queryClient.invalidateQueries({ queryKey: ['ai', 'kb', 'documents'] });
    },
    onError: (error) => {
      toast.error(`Upload failed: ${getApiErrorMessage(error)}`);
    },
  });

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files);
      files.forEach((file) => uploadMutation.mutate(file));
    },
    [uploadMutation],
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      files.forEach((file) => uploadMutation.mutate(file));
      if (fileInputRef.current) fileInputRef.current.value = '';
    },
    [uploadMutation],
  );

  return (
    <motion.div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      animate={{
        borderColor: isDragging ? 'hsl(var(--primary))' : 'hsl(var(--border))',
        backgroundColor: isDragging ? 'hsl(var(--primary) / 0.05)' : 'transparent',
      }}
      className="border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer"
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        multiple
        accept=".pdf,.doc,.docx,.txt,.md,.csv,.json"
        onChange={handleFileSelect}
      />
      <div className="flex flex-col items-center gap-3">
        {uploadMutation.isPending ? (
          <>
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
            <p className="text-sm font-medium">Uploading...</p>
          </>
        ) : (
          <>
            <UploadCloud className={`w-10 h-10 ${isDragging ? 'text-primary' : 'text-muted-foreground'}`} />
            <div>
              <p className="text-sm font-medium">
                {isDragging ? 'Drop files here' : 'Drag & drop files here, or click to browse'}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Supports PDF, DOC, DOCX, TXT, MD, CSV, JSON
              </p>
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}

// ─── Document Card ──────────────────────────────────────────────────

function DocumentCard({
  document,
  onEdit,
  onDelete,
  onView,
}: {
  document: ApiDocument;
  onEdit: (doc: ApiDocument) => void;
  onDelete: (doc: ApiDocument) => void;
  onView: (doc: ApiDocument) => void;
}) {
  const statusCfg = STATUS_CONFIG[document.status] ?? STATUS_CONFIG.pending;
  const StatusIcon = statusCfg.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      layout
    >
      <Card className="hover:shadow-md transition-shadow group">
        <CardContent className="p-5">
          {/* Header row */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 min-w-0 flex-1">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                <File className="w-5 h-5 text-primary" />
              </div>
              <div className="min-w-0 flex-1">
                <h3
                  className="font-semibold truncate cursor-pointer hover:text-primary transition-colors"
                  onClick={() => onView(document)}
                >
                  {document.title}
                </h3>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <Badge
                    variant="secondary"
                    className={`text-xs ${DOC_TYPE_COLORS[document.doc_type] ?? ''}`}
                  >
                    {document.doc_type}
                  </Badge>
                  <div className="flex items-center gap-1">
                    <StatusIcon
                      className={`w-3 h-3 ${statusCfg.color} ${
                        document.status === 'processing' ? 'animate-spin' : ''
                      }`}
                    />
                    <span className={`text-xs ${statusCfg.color}`}>
                      {document.status}
                    </span>
                  </div>
                  {document.source !== 'manual' && (
                    <Badge variant="outline" className="text-xs">
                      {document.source}
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onView(document)}>
                <Eye className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onEdit(document)}>
                <Edit3 className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={() => onDelete(document)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Content preview */}
          {document.content && (
            <p className="text-sm text-muted-foreground mt-3 line-clamp-2">
              {document.content}
            </p>
          )}
          {document.description && !document.content && (
            <p className="text-sm text-muted-foreground mt-3 line-clamp-2">
              {document.description}
            </p>
          )}

          {/* Footer stats */}
          <div className="flex items-center gap-4 mt-4 pt-3 border-t border-border/50 text-xs text-muted-foreground">
            <span>
              Created {new Date(document.created_at).toLocaleDateString()}
            </span>
            {document.file_size != null && (
              <span>{(document.file_size / 1024).toFixed(1)} KB</span>
            )}
            <span className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              {document.view_count}
            </span>
            {document.tags.length > 0 && (
              <div className="flex items-center gap-1">
                {document.tags.slice(0, 2).map((tag) => (
                  <Badge key={tag} variant="outline" className="text-[10px] px-1.5 py-0">
                    {tag}
                  </Badge>
                ))}
                {document.tags.length > 2 && (
                  <span className="text-[10px]">+{document.tags.length - 2}</span>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ─── View Document Dialog ───────────────────────────────────────────

function ViewDocumentDialog({
  document,
  open,
  onOpenChange,
}: {
  document: ApiDocument | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  // Fetch full document when viewing
  const { data: fullDoc } = useQuery({
    queryKey: queryKeys.ai.knowledgeBase.document(document?.id ?? ''),
    queryFn: () => aiService.getDocument(document!.id),
    enabled: open && !!document?.id,
  });

  const doc = fullDoc ?? document;
  if (!doc) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <File className="w-5 h-5 text-primary" />
            {doc.title}
          </DialogTitle>
          <DialogDescription className="sr-only">View document details and content.</DialogDescription>
        </DialogHeader>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge
            variant="secondary"
            className={DOC_TYPE_COLORS[doc.doc_type] ?? ''}
          >
            {doc.doc_type}
          </Badge>
          <Badge variant="outline">{doc.status}</Badge>
          <span className="text-xs text-muted-foreground">
            Source: {doc.source}
          </span>
          {doc.file_name && (
            <span className="text-xs text-muted-foreground">
              File: {doc.file_name}
            </span>
          )}
        </div>
        {doc.description && (
          <p className="text-sm text-muted-foreground">{doc.description}</p>
        )}
        <div className="flex-1 overflow-y-auto mt-2 p-4 bg-muted/30 rounded-lg">
          <pre className="text-sm whitespace-pre-wrap font-sans leading-relaxed">
            {doc.content ?? 'No content available.'}
          </pre>
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border/50">
          <span>Created: {new Date(doc.created_at).toLocaleString()}</span>
          <span>Updated: {new Date(doc.updated_at).toLocaleString()}</span>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Create / Edit Dialog ───────────────────────────────────────────

function DocumentFormDialog({
  document,
  open,
  onOpenChange,
}: {
  document: ApiDocument | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const isEditing = !!document;

  const [title, setTitle] = useState(document?.title ?? '');
  const [description, setDescription] = useState(document?.description ?? '');
  const [content, setContent] = useState(document?.content ?? '');
  const [docType, setDocType] = useState<ApiDocumentType>(document?.doc_type ?? 'guide');
  const [tags, setTags] = useState(document?.tags.join(', ') ?? '');

  // Reset form when document or open changes
  const prevDocRef = useRef(document);
  if (document !== prevDocRef.current) {
    prevDocRef.current = document;
    setTitle(document?.title ?? '');
    setDescription(document?.description ?? '');
    setContent(document?.content ?? '');
    setDocType(document?.doc_type ?? 'guide');
    setTags(document?.tags.join(', ') ?? '');
  }

  const createMutation = useMutation({
    mutationFn: (payload: ApiDocumentCreate) => aiService.createDocument(payload),
    onSuccess: () => {
      toast.success('Document created successfully');
      queryClient.invalidateQueries({ queryKey: queryKeys.ai.knowledgeBase.status });
      queryClient.invalidateQueries({ queryKey: ['ai', 'kb', 'documents'] });
      onOpenChange(false);
    },
    onError: (error) => {
      toast.error(`Failed to create document: ${getApiErrorMessage(error)}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: ApiDocumentUpdate) =>
      aiService.updateDocument(document!.id, payload),
    onSuccess: () => {
      toast.success('Document updated successfully');
      queryClient.invalidateQueries({ queryKey: queryKeys.ai.knowledgeBase.status });
      queryClient.invalidateQueries({ queryKey: ['ai', 'kb', 'documents'] });
      if (document) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.ai.knowledgeBase.document(document.id),
        });
      }
      onOpenChange(false);
    },
    onError: (error) => {
      toast.error(`Failed to update document: ${getApiErrorMessage(error)}`);
    },
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      toast.error('Title is required');
      return;
    }

    const parsedTags = tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    if (isEditing) {
      const payload: ApiDocumentUpdate = {
        title: title.trim(),
        description: description.trim() || undefined,
        content: content.trim() || undefined,
        doc_type: docType,
        tags: parsedTags.length > 0 ? parsedTags : undefined,
      };
      updateMutation.mutate(payload);
    } else {
      const payload: ApiDocumentCreate = {
        title: title.trim(),
        description: description.trim() || undefined,
        content: content.trim() || undefined,
        doc_type: docType,
        source: 'manual',
        tags: parsedTags.length > 0 ? parsedTags : undefined,
      };
      createMutation.mutate(payload);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit Document' : 'Create New Document'}
          </DialogTitle>
          <DialogDescription className="sr-only">Fill in the document details below.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Title *</label>
            <Input
              placeholder="Document title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          {/* Doc Type */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Type</label>
            <Select value={docType} onValueChange={(val) => setDocType(val as ApiDocumentType)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {DOC_TYPES.map((dt) => (
                  <SelectItem key={dt.value} value={dt.value}>
                    {dt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <Input
              placeholder="Brief description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {/* Content */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Content</label>
            <Textarea
              placeholder="Document content..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={10}
              className="resize-y min-h-[200px]"
            />
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Tags</label>
            <Input
              placeholder="Comma-separated tags (e.g. onboarding, setup)"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending} className="gap-2">
              {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              {isEditing ? 'Update Document' : 'Create Document'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─── Delete Confirmation ────────────────────────────────────────────

function DeleteDocumentDialog({
  document,
  open,
  onOpenChange,
}: {
  document: ApiDocument | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => aiService.deleteDocument(document!.id),
    onSuccess: () => {
      toast.success('Document deleted successfully');
      queryClient.invalidateQueries({ queryKey: queryKeys.ai.knowledgeBase.status });
      queryClient.invalidateQueries({ queryKey: ['ai', 'kb', 'documents'] });
      onOpenChange(false);
    },
    onError: (error) => {
      toast.error(`Failed to delete document: ${getApiErrorMessage(error)}`);
    },
  });

  if (!document) return null;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Document</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete &quot;{document.title}&quot;? This action
            cannot be undone and the document will be permanently removed from the
            knowledge base.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteMutation.isPending}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              deleteMutation.mutate();
            }}
            disabled={deleteMutation.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90 gap-2"
          >
            {deleteMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// ─── Document Grid Skeleton ─────────────────────────────────────────

function DocumentGridSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-5 space-y-3">
            <div className="flex items-start gap-3">
              <Skeleton className="w-10 h-10 rounded-xl" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/3" />
              </div>
            </div>
            <Skeleton className="h-10 w-full" />
            <div className="flex gap-4">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-3 w-16" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────

export default function KnowledgeBasePage() {
  const [search, setSearch] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState<string>('all');
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<ApiDocument | null>(null);

  // Build query filters
  const filters: Record<string, unknown> = {};
  if (search.trim()) filters.search = search.trim();
  if (docTypeFilter !== 'all') filters.doc_type = docTypeFilter;

  const { data: documentsData, isLoading } = useQuery({
    queryKey: queryKeys.ai.knowledgeBase.documents(filters),
    queryFn: () =>
      aiService.listDocuments({
        search: search.trim() || undefined,
        doc_type: docTypeFilter !== 'all' ? docTypeFilter : undefined,
        limit: 50,
      }),
  });

  const documents = documentsData?.documents ?? [];
  const total = documentsData?.total ?? 0;

  // ── Handlers ────────────────────────────────────────────────────

  const handleCreate = () => {
    setSelectedDocument(null);
    setFormDialogOpen(true);
  };

  const handleEdit = (doc: ApiDocument) => {
    setSelectedDocument(doc);
    setFormDialogOpen(true);
  };

  const handleView = (doc: ApiDocument) => {
    setSelectedDocument(doc);
    setViewDialogOpen(true);
  };

  const handleDelete = (doc: ApiDocument) => {
    setSelectedDocument(doc);
    setDeleteDialogOpen(true);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent-primary flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl lg:text-3xl font-bold">Knowledge Base</h1>
              <p className="text-sm text-muted-foreground">
                Manage documents and resources for AI-powered assistance
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" className="gap-2" onClick={() => document.getElementById('upload-zone')?.scrollIntoView({ behavior: 'smooth' })}>
              <Upload className="w-4 h-4" />
              Upload
            </Button>
            <Button className="gap-2" onClick={handleCreate}>
              <Plus className="w-4 h-4" />
              New Document
            </Button>
          </div>
        </div>

        {/* Status Overview */}
        <StatusOverview />

        {/* Search and Filter Bar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <Select value={docTypeFilter} onValueChange={setDocTypeFilter}>
            <SelectTrigger className="w-full sm:w-[180px]">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4" />
                <SelectValue placeholder="Filter by type" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {DOC_TYPES.map((dt) => (
                <SelectItem key={dt.value} value={dt.value}>
                  {dt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Results count */}
        {!isLoading && (
          <p className="text-sm text-muted-foreground">
            {total} document{total !== 1 ? 's' : ''} found
            {search && ` for "${search}"`}
            {docTypeFilter !== 'all' && ` in ${docTypeFilter}`}
          </p>
        )}

        {/* Upload Zone */}
        <div id="upload-zone">
          <UploadZone />
        </div>

        {/* Document Grid */}
        {isLoading ? (
          <DocumentGridSkeleton />
        ) : documents.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <AnimatePresence mode="popLayout">
              {documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onView={handleView}
                />
              ))}
            </AnimatePresence>
          </div>
        ) : (
          <Card className="py-16">
            <CardContent className="text-center">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium mb-2">No documents found</h3>
              <p className="text-muted-foreground mb-4">
                {search || docTypeFilter !== 'all'
                  ? 'Try adjusting your search or filters'
                  : 'Upload a file or create a new document to get started'}
              </p>
              <Button onClick={handleCreate} className="gap-2">
                <Plus className="w-4 h-4" />
                Create Document
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Dialogs */}
      <DocumentFormDialog
        document={selectedDocument}
        open={formDialogOpen}
        onOpenChange={setFormDialogOpen}
      />
      <ViewDocumentDialog
        document={selectedDocument}
        open={viewDialogOpen}
        onOpenChange={setViewDialogOpen}
      />
      <DeleteDocumentDialog
        document={selectedDocument}
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
      />
    </DashboardLayout>
  );
}
