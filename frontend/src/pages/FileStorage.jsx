import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Upload, FileText, HardDrive, Trash2, Download } from "lucide-react";
import { listDocuments, uploadDocument, deleteDocument, getStorageStats } from "@/services/fileStorageService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import DashboardLayout from "../components/layout/DashboardLayout";
import PageHeader from "../components/layout/PageHeader";

const FileStorage = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("documents"); // documents, factures-pdf, stats
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadData, setUploadData] = useState({
    type_document: "autre",
    entite_type: "facture",
    entite_id: "",
    description: "",
  });

  const { data: documents, isLoading } = useQuery(
    ["documents"],
    () => listDocuments(),
    { enabled: !!user && activeTab === "documents" }
  );

  const { data: stats } = useQuery(
    ["storage-stats"],
    () => getStorageStats(),
    { enabled: !!user && activeTab === "stats" }
  );

  const uploadMutation = useMutation(
    ({ file, typeDocument, entiteType, entiteId, description }) =>
      uploadDocument(file, typeDocument, entiteType, entiteId, description),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(["documents"]);
        queryClient.invalidateQueries(["storage-stats"]);
        toast.success("Document uploadé avec succès");
        setSelectedFile(null);
        setUploadData({
          type_document: "autre",
          entite_type: "facture",
          entite_id: "",
          description: "",
        });
      },
      onError: () => {
        toast.error("Erreur lors de l'upload");
      },
    }
  );

  const deleteMutation = useMutation(deleteDocument, {
    onSuccess: () => {
      queryClient.invalidateQueries(["documents"]);
      queryClient.invalidateQueries(["storage-stats"]);
      toast.success("Document supprimé");
    },
    onError: () => {
      toast.error("Erreur lors de la suppression");
    },
  });

  const handleFileSelect = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleUpload = (e) => {
    e.preventDefault();
    if (!selectedFile) {
      toast.error("Veuillez sélectionner un fichier");
      return;
    }
    uploadMutation.mutate({
      file: selectedFile,
      typeDocument: uploadData.type_document,
      entiteType: uploadData.entite_type,
      entiteId: uploadData.entite_id,
      description: uploadData.description,
    });
  };

  const handleDelete = (documentId) => {
    if (confirm("Êtes-vous sûr de vouloir supprimer ce document ?")) {
      deleteMutation.mutate(documentId);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  const getTypeBadge = (type) => {
    const variants = {
      facture: "success",
      contrat: "default",
      bon_livraison: "secondary",
      bon_commande: "outline",
      autre: "destructive",
    };
    return <Badge variant={variants[type] || "secondary"}>{type}</Badge>;
  };

  if (isLoading) return <DashboardLayout><div>Chargement...</div></DashboardLayout>;

  return (
    <DashboardLayout>
    <div data-testid="file-storage-page">
      <PageHeader
        icon={HardDrive}
        title="File Storage Enterprise"
        description="Gestion des documents et factures PDF"
        favoriteKey="file-storage"
        actions={
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={activeTab === "documents" ? "default" : "outline"}
              onClick={() => setActiveTab("documents")}
              className={activeTab === "documents" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-documents"
            >
              <FileText className="w-4 h-4 mr-2" />
              Documents
            </Button>
            <Button
              variant={activeTab === "factures-pdf" ? "default" : "outline"}
              onClick={() => setActiveTab("factures-pdf")}
              className={activeTab === "factures-pdf" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-factures-pdf"
            >
              <FileText className="w-4 h-4 mr-2" />
              Factures PDF
            </Button>
            <Button
              variant={activeTab === "stats" ? "default" : "outline"}
              onClick={() => setActiveTab("stats")}
              className={activeTab === "stats" ? "bg-[#FF6200] hover:bg-[#E65800]" : ""}
              data-testid="tab-stats"
            >
              <HardDrive className="w-4 h-4 mr-2" />
              Statistiques
            </Button>
          </div>
        }
      />

      {activeTab === "documents" && (
        <Card>
          <CardHeader>
            <CardTitle>Documents</CardTitle>
            <CardDescription>
              Gestion des documents de l'entreprise
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-6 p-4 border rounded-lg bg-gray-50 dark:bg-[#040f1a]/50">
              <h3 className="font-semibold mb-4">Uploader un nouveau document</h3>
              <form onSubmit={handleUpload} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Fichier</label>
                  <Input type="file" onChange={handleFileSelect} />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Type de document</label>
                    <select
                      value={uploadData.type_document}
                      onChange={(e) => setUploadData({ ...uploadData, type_document: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md"
                    >
                      <option value="facture">Facture</option>
                      <option value="contrat">Contrat</option>
                      <option value="bon_livraison">Bon de livraison</option>
                      <option value="bon_commande">Bon de commande</option>
                      <option value="autre">Autre</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Type d'entité</label>
                    <select
                      value={uploadData.entite_type}
                      onChange={(e) => setUploadData({ ...uploadData, entite_type: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md"
                    >
                      <option value="facture">Facture</option>
                      <option value="commande">Commande</option>
                      <option value="client">Client</option>
                      <option value="fournisseur">Fournisseur</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">ID Entité</label>
                    <Input
                      value={uploadData.entite_id}
                      onChange={(e) => setUploadData({ ...uploadData, entite_id: e.target.value })}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <Input
                    value={uploadData.description}
                    onChange={(e) => setUploadData({ ...uploadData, description: e.target.value })}
                  />
                </div>
                <Button type="submit" className="bg-[#0A2540] hover:bg-[#0A2540]/90">
                  <Upload className="w-4 h-4 mr-2" />
                  Uploader
                </Button>
              </form>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Nom</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Type</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Entité</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Taille</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Date</th>
                    <th className="text-left py-3 px-4 font-semibold text-[#0A2540] dark:text-white">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents?.map((doc) => (
                    <tr key={doc.document_id} className="border-b hover:bg-gray-50 dark:hover:bg-[#040f1a]/50">
                      <td className="py-3 px-4 font-medium">{doc.nom}</td>
                      <td className="py-3 px-4">{getTypeBadge(doc.type_document)}</td>
                      <td className="py-3 px-4">{doc.entite_type} - {doc.entite_id}</td>
                      <td className="py-3 px-4">{formatFileSize(doc.taille_octets)}</td>
                      <td className="py-3 px-4">{new Date(doc.created_at).toLocaleDateString()}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm">
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(doc.document_id)}
                          >
                            <Trash2 className="w-4 h-4 text-red-600" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {documents?.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-white/50">
                  Aucun document trouvé
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "factures-pdf" && (
        <Card>
          <CardHeader>
            <CardTitle>Factures PDF</CardTitle>
            <CardDescription>
              Gestion des factures au format PDF
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500 dark:text-white/50">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Module en cours de développement</p>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "stats" && (
        <Card>
          <CardHeader>
            <CardTitle>Statistiques de Stockage</CardTitle>
            <CardDescription>
              Informations sur l'utilisation du stockage
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="p-4 border rounded-lg">
                <div className="text-3xl font-bold text-[#0A2540] dark:text-white">
                  {stats?.total_size_mb?.toFixed(2)} MB
                </div>
                <p className="text-sm text-gray-500 dark:text-white/50 mt-2">Espace utilisé</p>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="text-3xl font-bold text-[#0A2540] dark:text-white">
                  {stats?.file_count}
                </div>
                <p className="text-sm text-gray-500 dark:text-white/50 mt-2">Fichiers stockés</p>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="text-3xl font-bold text-[#0A2540] dark:text-white">
                  {stats?.total_documents}
                </div>
                <p className="text-sm text-gray-500 dark:text-white/50 mt-2">Documents en base</p>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="text-3xl font-bold text-[#0A2540] dark:text-white">
                  {stats?.total_factures_pdf}
                </div>
                <p className="text-sm text-gray-500 dark:text-white/50 mt-2">Factures PDF</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </DashboardLayout>
  );
};

export default FileStorage;
