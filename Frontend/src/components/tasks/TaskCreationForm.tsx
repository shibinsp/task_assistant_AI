import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Save, Send, Loader2, X } from 'lucide-react';
import type { ApiTaskCreate, ApiTaskPriority } from '@/types/api';

interface TaskCreationFormProps {
  initialData?: Partial<ApiTaskCreate> & { id?: string };
  onSaveDraft: (data: ApiTaskCreate) => void;
  onPublish: (data: ApiTaskCreate) => void;
  onCancel?: () => void;
  isSubmitting: boolean;
}

export function TaskCreationForm({
  initialData,
  onSaveDraft,
  onPublish,
  onCancel,
  isSubmitting,
}: TaskCreationFormProps) {
  const [title, setTitle] = useState(initialData?.title ?? '');
  const [description, setDescription] = useState(initialData?.description ?? '');
  const [priority, setPriority] = useState<ApiTaskPriority>(initialData?.priority ?? 'medium');
  const [deadline, setDeadline] = useState(initialData?.deadline ?? '');
  const [estimatedHours, setEstimatedHours] = useState<string>(
    initialData?.estimated_hours?.toString() ?? ''
  );
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>(initialData?.tags ?? []);

  const isEditing = !!initialData?.id;

  const buildPayload = (): ApiTaskCreate => ({
    title: title.trim(),
    description: description.trim() || undefined,
    priority,
    deadline: deadline || undefined,
    estimated_hours: estimatedHours ? parseFloat(estimatedHours) : undefined,
    tags: tags.length > 0 ? tags : undefined,
  });

  const handleTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if ((e.key === 'Enter' || e.key === ',') && tagInput.trim()) {
      e.preventDefault();
      const newTag = tagInput.trim().toLowerCase();
      if (!tags.includes(newTag)) {
        setTags([...tags, newTag]);
      }
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setPriority('medium');
    setDeadline('');
    setEstimatedHours('');
    setTags([]);
    setTagInput('');
  };

  const handleSaveDraft = () => {
    onSaveDraft(buildPayload());
    if (!isEditing) resetForm();
  };

  const handlePublish = () => {
    onPublish(buildPayload());
    resetForm();
  };

  return (
    <div className="space-y-4 p-4">
      {isEditing && onCancel && (
        <div className="flex items-center justify-between pb-2 border-b border-border/50">
          <span className="text-sm text-muted-foreground">Editing draft</span>
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Cancel editing
          </Button>
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="task-title">Title *</Label>
        <Input
          id="task-title"
          placeholder="What needs to be done?"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          autoFocus
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="task-description">Description</Label>
        <Textarea
          id="task-description"
          placeholder="Add details, context, or acceptance criteria..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>Priority</Label>
          <Select value={priority} onValueChange={(v) => setPriority(v as ApiTaskPriority)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="task-hours">Estimated Hours</Label>
          <Input
            id="task-hours"
            type="number"
            min="0"
            step="0.5"
            placeholder="0"
            value={estimatedHours}
            onChange={(e) => setEstimatedHours(e.target.value)}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="task-deadline">Deadline</Label>
        <Input
          id="task-deadline"
          type="datetime-local"
          value={deadline}
          onChange={(e) => setDeadline(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="task-tags">Tags</Label>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="gap-1 pr-1">
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="ml-0.5 rounded-full hover:bg-muted-foreground/20 p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
        </div>
        <Input
          id="task-tags"
          placeholder="Type a tag and press Enter..."
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyDown={handleTagKeyDown}
        />
      </div>

      <div className="flex gap-2 pt-4 border-t border-border/50">
        <Button
          variant="outline"
          className="flex-1 gap-2"
          onClick={handleSaveDraft}
          disabled={!title.trim() || isSubmitting}
        >
          {isSubmitting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {isEditing ? 'Update Draft' : 'Save Draft'}
        </Button>
        <Button
          className="flex-1 gap-2"
          onClick={handlePublish}
          disabled={!title.trim() || isSubmitting}
        >
          {isSubmitting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
          {isEditing ? 'Publish' : 'Create Task'}
        </Button>
      </div>
    </div>
  );
}
