import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { TaskCreationForm } from './TaskCreationForm';
import { DraftsList } from './DraftsList';
import { tasksService } from '@/services/tasks.service';
import { queryKeys } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';
import { toast } from 'sonner';
import { getApiErrorMessage } from '@/lib/api-client';
import type { ApiTask, ApiTaskCreate } from '@/types/api';

export function TaskCreationSidebar() {
  const { taskCreationSidebarOpen, setTaskCreationSidebarOpen } = useUIStore();
  const [activeTab, setActiveTab] = useState<string>('create');
  const [editingDraft, setEditingDraft] = useState<ApiTask | null>(null);
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (payload: ApiTaskCreate) => tasksService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      toast.success('Task created');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const saveDraftMutation = useMutation({
    mutationFn: (payload: ApiTaskCreate) =>
      tasksService.create({ ...payload, is_draft: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.drafts() });
      toast.success('Draft saved');
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const updateDraftMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ApiTaskCreate }) =>
      tasksService.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.drafts() });
      toast.success('Draft updated');
      setEditingDraft(null);
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const publishDraftMutation = useMutation({
    mutationFn: (taskId: string) => tasksService.publishDraft(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all });
      toast.success('Task published');
      setEditingDraft(null);
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const handleSaveDraft = (data: ApiTaskCreate) => {
    if (editingDraft) {
      updateDraftMutation.mutate({ id: editingDraft.id, payload: data });
    } else {
      saveDraftMutation.mutate(data);
    }
  };

  const handlePublish = (data: ApiTaskCreate) => {
    if (editingDraft) {
      // Update the draft first, then publish
      tasksService.update(editingDraft.id, data).then(() => {
        publishDraftMutation.mutate(editingDraft.id);
      });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleEditDraft = (task: ApiTask) => {
    setEditingDraft(task);
    setActiveTab('create');
  };

  const isSubmitting =
    createMutation.isPending ||
    saveDraftMutation.isPending ||
    updateDraftMutation.isPending ||
    publishDraftMutation.isPending;

  return (
    <AnimatePresence>
      {taskCreationSidebarOpen && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="fixed right-0 top-16 bottom-0 w-[400px] bg-card border-l border-border/50 z-20 flex flex-col shadow-xl"
        >
          {/* Header */}
          <div className="h-14 flex items-center justify-between px-4 border-b border-border/50 shrink-0">
            <h2 className="font-semibold">Task Creator</h2>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => {
                setTaskCreationSidebarOpen(false);
                setEditingDraft(null);
              }}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col flex-1 min-h-0">
            <TabsList className="w-full rounded-none border-b border-border/50 bg-transparent h-10 shrink-0">
              <TabsTrigger value="create" className="flex-1 data-[state=active]:bg-muted rounded-none">
                Create
              </TabsTrigger>
              <TabsTrigger value="drafts" className="flex-1 data-[state=active]:bg-muted rounded-none">
                Drafts
              </TabsTrigger>
            </TabsList>

            <TabsContent value="create" className="flex-1 overflow-y-auto mt-0">
              <TaskCreationForm
                key={editingDraft?.id ?? 'new'}
                initialData={
                  editingDraft
                    ? {
                        id: editingDraft.id,
                        title: editingDraft.title,
                        description: editingDraft.description,
                        priority: editingDraft.priority,
                        deadline: editingDraft.deadline,
                        estimated_hours: editingDraft.estimated_hours,
                        tags: editingDraft.tags,
                      }
                    : undefined
                }
                onSaveDraft={handleSaveDraft}
                onPublish={handlePublish}
                onCancel={editingDraft ? () => setEditingDraft(null) : undefined}
                isSubmitting={isSubmitting}
              />
            </TabsContent>

            <TabsContent value="drafts" className="flex-1 overflow-y-auto mt-0">
              <DraftsList onEditDraft={handleEditDraft} />
            </TabsContent>
          </Tabs>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
