import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksService } from '@/services/tasks.service';
import { queryKeys } from '@/hooks/useApi';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Pencil, Send, Trash2, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { getApiErrorMessage } from '@/lib/api-client';
import type { ApiTask } from '@/types/api';

const priorityColors: Record<string, string> = {
  low: 'bg-slate-500/10 text-slate-600',
  medium: 'bg-blue-500/10 text-blue-600',
  high: 'bg-orange-500/10 text-orange-600',
  critical: 'bg-red-500/10 text-red-600',
};

export function DraftsList({ onEditDraft }: { onEditDraft: (task: ApiTask) => void }) {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.tasks.drafts(),
    queryFn: () => tasksService.listDrafts({ limit: 50 }),
  });

  const publishMutation = useMutation({
    mutationFn: (taskId: string) => tasksService.publishDraft(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      toast.success('Task published');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (taskId: string) => tasksService.delete(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.drafts() });
      toast.success('Draft deleted');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const drafts = data?.tasks ?? [];

  if (isLoading) {
    return (
      <div className="p-4 space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (drafts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <FileText className="w-10 h-10 text-muted-foreground/40 mb-3" />
        <p className="text-sm font-medium text-muted-foreground">No drafts yet</p>
        <p className="text-xs text-muted-foreground/70 mt-1">
          Save a task as draft to continue working on it later.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <p className="text-xs text-muted-foreground">
        {drafts.length} draft{drafts.length !== 1 ? 's' : ''}
      </p>
      {drafts.map((draft) => (
        <div
          key={draft.id}
          className="rounded-lg border border-border/50 p-3 space-y-2 hover:border-border transition-colors"
        >
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-sm font-medium line-clamp-2 flex-1">{draft.title}</h4>
            <Badge
              variant="secondary"
              className={`text-[10px] shrink-0 ${priorityColors[draft.priority] ?? ''}`}
            >
              {draft.priority}
            </Badge>
          </div>
          {draft.description && (
            <p className="text-xs text-muted-foreground line-clamp-2">{draft.description}</p>
          )}
          <div className="flex items-center justify-between pt-1">
            <span className="text-[10px] text-muted-foreground">
              {new Date(draft.created_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              })}
            </span>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => onEditDraft(draft)}
                title="Edit"
              >
                <Pencil className="w-3.5 h-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-primary"
                onClick={() => publishMutation.mutate(draft.id)}
                disabled={publishMutation.isPending}
                title="Publish"
              >
                <Send className="w-3.5 h-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-destructive"
                onClick={() => deleteMutation.mutate(draft.id)}
                disabled={deleteMutation.isPending}
                title="Delete"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
