import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { MessageSquare, Mail, Send, CheckCircle, XCircle, Settings, AlertTriangle } from "lucide-react";
import { sendSMS, sendWhatsApp, sendEmail, sendBatchNotifications, checkConfiguration } from "@/services/multiChannelNotificationsService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";

const MultiChannelNotifications = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("sms"); // sms, whatsapp, email, batch, config
  const [showSend, setShowSend] = useState(false);
  const [formData, setFormData] = useState({
    destinataire: "",
    message: "",
    canal: "twilio",
    sujet: "",
    corps_html: "",
    corps_texte: "",
  });

  const { data: config, isLoading: loadingConfig } = useQuery(
    ["notification-config"],
    checkConfiguration
  );

  const sendSMSMutation = useMutation(sendSMS, {
    onSuccess: () => {
      queryClient.invalidateQueries(["notification-logs"]);
      toast.success("SMS envoyé avec succès");
      setShowSend(false);
      setFormData({ destinataire: "", message: "", canal: "twilio", sujet: "", corps_html: "", corps_texte: "" });
    },
    onError: (error) => {
      toast.error(`Erreur: ${error.response?.data?.detail || "Échec de l'envoi"}`);
    },
  });

  const sendWhatsAppMutation = useMutation(sendWhatsApp, {
    onSuccess: () => {
      queryClient.invalidateQueries(["notification-logs"]);
      toast.success("Message WhatsApp envoyé avec succès");
      setShowSend(false);
      setFormData({ destinataire: "", message: "", canal: "twilio", sujet: "", corps_html: "", corps_texte: "" });
    },
    onError: (error) => {
      toast.error(`Erreur: ${error.response?.data?.detail || "Échec de l'envoi"}`);
    },
  });

  const sendEmailMutation = useMutation(sendEmail, {
    onSuccess: () => {
      queryClient.invalidateQueries(["notification-logs"]);
      toast.success("Email envoyé avec succès");
      setShowSend(false);
      setFormData({ destinataire: "", message: "", canal: "twilio", sujet: "", corps_html: "", corps_texte: "" });
    },
    onError: (error) => {
      toast.error(`Erreur: ${error.response?.data?.detail || "Échec de l'envoi"}`);
    },
  });

  const handleSendSMS = (e) => {
    e.preventDefault();
    sendSMSMutation.mutate({
      destinataire: formData.destinataire,
      message: formData.message,
      canal: formData.canal,
    });
  };

  const handleSendWhatsApp = (e) => {
    e.preventDefault();
    sendWhatsAppMutation.mutate({
      destinataire: formData.destinataire,
      message: formData.message,
    });
  };

  const handleSendEmail = (e) => {
    e.preventDefault();
    sendEmailMutation.mutate({
      destinataire: formData.destinataire,
      sujet: formData.sujet,
      corps_html: formData.corps_html,
      corps_texte: formData.corps_texte,
    });
  };

  if (loadingConfig) return <div className="p-8">Chargement...</div>;

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#0A2540] dark:text-white">Notifications Multi-Canaux</h1>
          <p className="text-[#0A2540]/60 dark:text-white/60 mt-1">SMS, WhatsApp, Email</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={activeTab === "sms" ? "default" : "outline"}
            onClick={() => setActiveTab("sms")}
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            SMS
          </Button>
          <Button
            variant={activeTab === "whatsapp" ? "default" : "outline"}
            onClick={() => setActiveTab("whatsapp")}
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            WhatsApp
          </Button>
          <Button
            variant={activeTab === "email" ? "default" : "outline"}
            onClick={() => setActiveTab("email")}
          >
            <Mail className="w-4 h-4 mr-2" />
            Email
          </Button>
          <Button
            variant={activeTab === "batch" ? "default" : "outline"}
            onClick={() => setActiveTab("batch")}
          >
            <Send className="w-4 h-4 mr-2" />
            Batch
          </Button>
          <Button
            variant={activeTab === "config" ? "default" : "outline"}
            onClick={() => setActiveTab("config")}
          >
            <Settings className="w-4 h-4 mr-2" />
            Configuration
          </Button>
        </div>
      </div>

      {activeTab === "sms" && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Envoyer un SMS</CardTitle>
              <Dialog open={showSend} onOpenChange={setShowSend}>
                <DialogTrigger asChild>
                  <Button className="bg-[#0A2540] hover:bg-[#0A2540]/90">
                    <Send className="w-4 h-4 mr-2" />
                    Nouveau SMS
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-md">
                  <DialogHeader>
                    <DialogTitle>Envoyer un SMS</DialogTitle>
                    <DialogDescription>
                      Sélectionnez le canal et saisissez le message
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleSendSMS} className="space-y-4">
                    <div>
                      <Label>Destinataire (numéro avec indicatif, ex: +22507XXXXXXXX)</Label>
                      <Input
                        value={formData.destinataire}
                        onChange={(e) => setFormData({ ...formData, destinataire: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <Label>Canal SMS</Label>
                      <select
                        value={formData.canal}
                        onChange={(e) => setFormData({ ...formData, canal: e.target.value })}
                        className="w-full px-3 py-2 border rounded-md"
                        required
                      >
                        <option value="twilio">Twilio (International)</option>
                        <option value="orange_ci">Orange CI</option>
                        <option value="mtn_ci">MTN CI</option>
                      </select>
                    </div>
                    <div>
                      <Label>Message</Label>
                      <textarea
                        value={formData.message}
                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                        className="w-full px-3 py-2 border rounded-md min-h-[100px]"
                        required
                        maxLength={160}
                      />
                      <p className="text-xs text-gray-500 dark:text-white/50 mt-1">{formData.message.length}/160 caractères</p>
                    </div>
                    <Button type="submit" className="w-full bg-[#0A2540] hover:bg-[#0A2540]/90">
                      Envoyer le SMS
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500 dark:text-white/50">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Utilisez le bouton pour envoyer un nouveau SMS</p>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "whatsapp" && (
        <Card>
          <CardHeader>
            <CardTitle>Envoyer un message WhatsApp</CardTitle>
            <Dialog open={showSend} onOpenChange={setShowSend}>
              <DialogTrigger asChild>
                <Button className="bg-[#0A2540] hover:bg-[#0A2540]/90">
                  <Send className="w-4 h-4 mr-2" />
                  Nouveau Message
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Envoyer un message WhatsApp</DialogTitle>
                  <DialogDescription>
                    Saissez le numéro et le message
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSendWhatsApp} className="space-y-4">
                  <div>
                    <Label>Destinataire (numéro avec indicatif)</Label>
                    <Input
                      value={formData.destinataire}
                      onChange={(e) => setFormData({ ...formData, destinataire: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label>Message</Label>
                    <textarea
                      value={formData.message}
                      onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md min-h-[100px]"
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full bg-[#0A2540] hover:bg-[#0A2540]/90">
                    Envoyer WhatsApp
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500 dark:text-white/50">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Utilisez le bouton pour envoyer un message WhatsApp</p>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "email" && (
        <Card>
          <CardHeader>
            <CardTitle>Envoyer un Email</CardTitle>
            <Dialog open={showSend} onOpenChange={setShowSend}>
              <DialogTrigger asChild>
                <Button className="bg-[#0A2540] hover:bg-[#0A2540]/90">
                  <Send className="w-4 h-4 mr-2" />
                  Nouvel Email
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Envoyer un Email</DialogTitle>
                  <DialogDescription>
                    Saissez les détails de l'email
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSendEmail} className="space-y-4">
                  <div>
                    <Label>Destinataire</Label>
                    <Input
                      type="email"
                      value={formData.destinataire}
                      onChange={(e) => setFormData({ ...formData, destinataire: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label>Sujet</Label>
                    <Input
                      value={formData.sujet}
                      onChange={(e) => setFormData({ ...formData, sujet: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label>Corps (Texte)</Label>
                    <textarea
                      value={formData.corps_texte}
                      onChange={(e) => setFormData({ ...formData, corps_texte: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md min-h-[100px]"
                      required
                    />
                  </div>
                  <div>
                    <Label>Corps (HTML)</Label>
                    <textarea
                      value={formData.corps_html}
                      onChange={(e) => setFormData({ ...formData, corps_html: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md min-h-[100px]"
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full bg-[#0A2540] hover:bg-[#0A2540]/90">
                    Envoyer l'Email
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500 dark:text-white/50">
              <Mail className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Utilisez le bouton pour envoyer un email</p>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "batch" && (
        <Card>
          <CardHeader>
            <CardTitle>Notifications en Lot</CardTitle>
            <CardDescription>
              Envoyer des notifications à plusieurs destinataires
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500 dark:text-white/50">
              <Send className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Module en cours de développement</p>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "config" && (
        <Card>
          <CardHeader>
            <CardTitle>Configuration des APIs</CardTitle>
            <CardDescription>
              Vérifiez la configuration des APIs de notification
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-semibold">Twilio SMS</h3>
                  <p className="text-sm text-gray-500 dark:text-white/50">SMS international</p>
                </div>
                <Badge variant={config?.twilio?.configured ? "success" : "destructive"}>
                  {config?.twilio?.configured ? "Configuré" : "Non configuré"}
                </Badge>
              </div>
              {!config?.twilio?.configured && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <AlertTriangle className="w-4 h-4 inline mr-2" />
                    Variables manquantes: {config?.twilio?.missing?.join(", ")}
                  </p>
                </div>
              )}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-semibold">Orange CI SMS</h3>
                  <p className="text-sm text-gray-500 dark:text-white/50">SMS local Côte d'Ivoire</p>
                </div>
                <Badge variant={config?.orange_ci?.configured ? "success" : "destructive"}>
                  {config?.orange_ci?.configured ? "Configuré" : "Non configuré"}
                </Badge>
              </div>
              {!config?.orange_ci?.configured && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <AlertTriangle className="w-4 h-4 inline mr-2" />
                    Variables manquantes: {config?.orange_ci?.missing?.join(", ")}
                  </p>
                </div>
              )}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-semibold">MTN CI SMS</h3>
                  <p className="text-sm text-gray-500 dark:text-white/50">SMS local Côte d'Ivoire</p>
                </div>
                <Badge variant={config?.mtn_ci?.configured ? "success" : "destructive"}>
                  {config?.mtn_ci?.configured ? "Configuré" : "Non configuré"}
                </Badge>
              </div>
              {!config?.mtn_ci?.configured && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <AlertTriangle className="w-4 h-4 inline mr-2" />
                    Variables manquantes: {config?.mtn_ci?.missing?.join(", ")}
                  </p>
                </div>
              )}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-semibold">WhatsApp Business</h3>
                  <p className="text-sm text-gray-500 dark:text-white/50">Messages WhatsApp</p>
                </div>
                <Badge variant={config?.whatsapp?.configured ? "success" : "destructive"}>
                  {config?.whatsapp?.configured ? "Configuré" : "Non configuré"}
                </Badge>
              </div>
              {!config?.whatsapp?.configured && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <AlertTriangle className="w-4 h-4 inline mr-2" />
                    Variables manquantes: {config?.whatsapp?.missing?.join(", ")}
                  </p>
                </div>
              )}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-semibold">Email SMTP</h3>
                  <p className="text-sm text-gray-500 dark:text-white/50">Envoi d'emails</p>
                </div>
                <Badge variant={config?.email?.configured ? "success" : "destructive"}>
                  {config?.email?.configured ? "Configuré" : "Non configuré"}
                </Badge>
              </div>
              {!config?.email?.configured && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <AlertTriangle className="w-4 h-4 inline mr-2" />
                    Variables manquantes: {config?.email?.missing?.join(", ")}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MultiChannelNotifications;
