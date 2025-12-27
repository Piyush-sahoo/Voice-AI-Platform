import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Upload, Link, FileText, AlignLeft } from "lucide-react";
import { mockAgents } from "@/data/mockAgents";
import { KnowledgeItem } from "@/data/mockKnowledge";
import { toast } from "sonner";

interface UploadKnowledgeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpload: (knowledge: Partial<KnowledgeItem>) => void;
}

export function UploadKnowledgeDialog({
  open,
  onOpenChange,
  onUpload,
}: UploadKnowledgeDialogProps) {
  const [uploadType, setUploadType] = useState<"file" | "url" | "text">("file");
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file: File) => {
    const validTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
    ];

    if (!validTypes.includes(file.type)) {
      toast.error("Invalid file type. Please upload PDF, DOCX, or TXT files.");
      return;
    }

    setSelectedFile(file);
    if (!name) {
      setName(file.name.replace(/\.[^/.]+$/, ""));
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const toggleAgent = (agentId: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agentId)
        ? prev.filter((id) => id !== agentId)
        : [...prev, agentId]
    );
  };

  const handleSubmit = () => {
    if (!name.trim()) {
      toast.error("Please enter a name for the knowledge base");
      return;
    }

    if (uploadType === "file" && !selectedFile) {
      toast.error("Please select a file to upload");
      return;
    }

    if (uploadType === "url" && !url.trim()) {
      toast.error("Please enter a URL");
      return;
    }

    if (uploadType === "text" && !text.trim()) {
      toast.error("Please enter some text");
      return;
    }

    const fileType =
      uploadType === "file"
        ? selectedFile?.name.endsWith(".pdf")
          ? "pdf"
          : selectedFile?.name.endsWith(".docx")
          ? "docx"
          : "txt"
        : uploadType === "url"
        ? "url"
        : "text";

    onUpload({
      name: name.trim(),
      type: fileType,
      size: selectedFile?.size || text.length || url.length,
      assignedAgents: selectedAgents,
      status: "processing",
    });

    // Reset form
    setName("");
    setUrl("");
    setText("");
    setSelectedAgents([]);
    setSelectedFile(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-foreground">Upload Knowledge</DialogTitle>
          <DialogDescription>
            Add documents, URLs, or text to your knowledge base
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-foreground">Knowledge Name *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Product Documentation"
              className="bg-background border-border text-foreground"
            />
          </div>

          <Tabs value={uploadType} onValueChange={(v) => setUploadType(v as typeof uploadType)}>
            <TabsList className="grid w-full grid-cols-3 bg-muted">
              <TabsTrigger value="file" className="gap-2 data-[state=active]:bg-background">
                <Upload className="h-4 w-4" />
                File
              </TabsTrigger>
              <TabsTrigger value="url" className="gap-2 data-[state=active]:bg-background">
                <Link className="h-4 w-4" />
                URL
              </TabsTrigger>
              <TabsTrigger value="text" className="gap-2 data-[state=active]:bg-background">
                <AlignLeft className="h-4 w-4" />
                Text
              </TabsTrigger>
            </TabsList>

            <TabsContent value="file" className="mt-4">
              <div
                className={`relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
                  dragActive
                    ? "border-primary bg-primary/5"
                    : selectedFile
                    ? "border-primary/50 bg-primary/5"
                    : "border-border bg-muted/50 hover:border-muted-foreground"
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileInput}
                  className="absolute inset-0 cursor-pointer opacity-0"
                />
                {selectedFile ? (
                  <div className="flex flex-col items-center gap-2">
                    <FileText className="h-10 w-10 text-primary" />
                    <p className="font-medium text-foreground">{selectedFile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2 text-center">
                    <Upload className="h-10 w-10 text-muted-foreground" />
                    <p className="font-medium text-foreground">Drop file here or click to browse</p>
                    <p className="text-sm text-muted-foreground">
                      Supports PDF, DOCX, TXT
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="url" className="mt-4">
              <div className="space-y-2">
                <Label htmlFor="url" className="text-foreground">Website URL</Label>
                <Input
                  id="url"
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="bg-background border-border text-foreground"
                />
                <p className="text-xs text-muted-foreground">
                  We'll crawl and extract content from this URL
                </p>
              </div>
            </TabsContent>

            <TabsContent value="text" className="mt-4">
              <div className="space-y-2">
                <Label htmlFor="text" className="text-foreground">Raw Text</Label>
                <Textarea
                  id="text"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste your text content here..."
                  rows={6}
                  className="bg-background border-border text-foreground"
                />
              </div>
            </TabsContent>
          </Tabs>

          <div className="space-y-3">
            <Label className="text-foreground">Assign to Agents (Optional)</Label>
            <ScrollArea className="h-32 rounded-lg border border-border bg-muted/50 p-3">
              <div className="space-y-2">
                {mockAgents.map((agent) => (
                  <div
                    key={agent.id}
                    className="flex items-center gap-3 rounded-md p-2 hover:bg-accent"
                  >
                    <Checkbox
                      id={agent.id}
                      checked={selectedAgents.includes(agent.id)}
                      onCheckedChange={() => toggleAgent(agent.id)}
                    />
                    <label
                      htmlFor={agent.id}
                      className="flex-1 cursor-pointer text-sm font-medium text-foreground"
                    >
                      {agent.name}
                    </label>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>

          <div className="flex gap-3">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button className="flex-1" onClick={handleSubmit}>
              Upload
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
