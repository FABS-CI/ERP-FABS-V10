/**
 * Composant de formulaire nouvelle commande - 3 étapes
 * Sprint 6
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Save, Send, Plus, Trash2, ChevronsUpDown, Check } from 'lucide-react';
import { createCommande, updateCommande, getCommande, checkDoublon, logDoublonDecision } from '../../services/commandesApi';
import { listClients } from '../../services/clientsApi';
import { listProducts } from '../../services/produitsApi';
import DoublonAlert from './DoublonAlert';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { Command, CommandEmpty, CommandInput, CommandItem, CommandList } from '../ui/command';
import { Separator } from '../ui/separator';
import { Badge } from '../ui/badge';
import { toast } from 'sonner';
import DashboardLayout from '../layout/DashboardLayout';
import ClientPicker from './ClientPicker';

export default function CommandeForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { id: editId } = useParams();
  const isEdit = Boolean(editId);
  const preloadClientId = searchParams.get('client_id') || '';

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState([]);
  const [produits, setProduits] = useState([]);
  const [loadingProduits, setLoadingProduits] = useState(false);
  const [openProduitIdx, setOpenProduitIdx] = useState(null);

  const [formData, setFormData] = useState({
    client_id: preloadClientId,
    date_livraison_prevue: '',
    remise_globale: 0,
    notes: '',
    lignes: [],
  });

  const [selectedClient, setSelectedClient] = useState(null);

  // --- Doublon detection ---
  const [doublonData, setDoublonData] = useState(null);   // { commande, niveau, logId }
  const [showDoublonAlert, setShowDoublonAlert] = useState(false);
  const doublonTimerRef = useRef(null);
  const skipDoublonCheck = useRef(false); // flag "continuer quand même"

  useEffect(() => {
    fetchClients();
    fetchProduits();
  }, []);

  // Mode édition : précharger la commande existante (brouillon uniquement)
  useEffect(() => {
    if (!editId) return;
    (async () => {
      try {
        const cmd = await getCommande(editId);
        if (cmd.statut && cmd.statut !== 'brouillon') {
          toast.error('Seules les commandes en brouillon peuvent être modifiées');
          navigate(`/commandes/${editId}`);
          return;
        }
        setFormData({
          client_id: cmd.client_id || '',
          date_livraison_prevue: cmd.date_livraison_prevue
            ? String(cmd.date_livraison_prevue).slice(0, 10)
            : '',
          remise_globale: cmd.remise_globale || 0,
          notes: cmd.notes || '',
          lignes: (cmd.lignes || []).map((l) => ({
            produit_id: l.produit_id || l.product_id || '',
            quantite: l.quantite || 1,
            prix_unitaire: l.prix_unitaire || 0,
            remise_ligne: l.remise_ligne || 0,
          })),
        });
      } catch (error) {
        toast.error('Impossible de charger la commande à modifier');
        navigate('/commandes');
      }
    })();
  }, [editId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Mode édition : résoudre le client sélectionné une fois la liste clients chargée
  useEffect(() => {
    if (!isEdit || !formData.client_id || clients.length === 0) return;
    if (selectedClient?.client_id === formData.client_id) return;
    const found = clients.find((c) => c.client_id === formData.client_id);
    if (found) setSelectedClient(found);
  }, [isEdit, formData.client_id, clients]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchClients = async () => {
    try {
      // Charger toutes les pages pour avoir la liste complète
      let allClients = [];
      let page = 1;
      const pageSize = 500;
      while (true) {
        const data = await listClients({ actif: true, page_size: pageSize, page });
        const items = Array.isArray(data) ? data : (data?.items || []);
        allClients = [...allClients, ...items];
        const total = data?.total ?? items.length;
        if (allClients.length >= total || items.length < pageSize) break;
        page++;
      }
      setClients(allClients);
      // Précharger le client si client_id dans l'URL
      if (preloadClientId) {
        const found = allClients.find(c => c.client_id === preloadClientId);
        if (found) {
          setSelectedClient(found);
          setFormData(prev => ({ ...prev, client_id: preloadClientId }));
        }
      }
    } catch (error) {
      toast.error('Erreur chargement clients');
      setClients([]);
    }
  };

  const fetchProduits = async () => {
    setLoadingProduits(true);
    try {
      const data = await listProducts({ actif: true, page_size: 100 });
      const items = Array.isArray(data) ? data : (data?.items || []);
      setProduits(items);
    } catch (error) {
      toast.error('Erreur chargement produits: ' + (error.response?.data?.detail || error.message));
      setProduits([]);
    } finally {
      setLoadingProduits(false);
    }
  };

  const handleClientSelect = (clientId) => {
    const client = clients.find(c => c.client_id === clientId);
    setSelectedClient(client);
    setFormData(prev => ({ ...prev, client_id: clientId }));
  };

  // --- Doublon detection debounce (800ms) ---
  const triggerDoublonCheck = useCallback((data) => {
    if (doublonTimerRef.current) clearTimeout(doublonTimerRef.current);

    // Mode édition : on modifie une commande existante, pas de détection de doublon
    if (isEdit) return;

    // Pas assez d'infos pour vérifier
    if (!data.client_id || data.lignes.length === 0) return;

    // Vérifier que toutes les lignes sont complètes
    const lignesComplete = data.lignes.every(
      (l) => l.produit_id && l.quantite > 0 && l.prix_unitaire > 0
    );
    if (!lignesComplete) return;

    // Si l'utilisateur a choisi "continuer quand même", ne pas re-checker
    if (skipDoublonCheck.current) return;

    doublonTimerRef.current = setTimeout(async () => {
      try {
        const result = await checkDoublon({
          client_id: data.client_id,
          lignes: data.lignes,
          representant: selectedClient?.representant || null,
          telephone: selectedClient?.telephone || null,
        });

        if (result.doublon) {
          setDoublonData({ commande: result.commande, niveau: result.niveau, logId: result.log_id });
          setShowDoublonAlert(true);
        }
      } catch (err) {
        // Silencieux — ne pas bloquer la saisie
        console.warn('Doublon check error:', err);
      }
    }, 800);
  }, [selectedClient, isEdit]);

  // Déclencher le check quand client ou lignes changent
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    triggerDoublonCheck(formData);
  }, [formData.client_id, formData.lignes, triggerDoublonCheck]);

  // Réinitialiser le flag "skip" quand le client change
  useEffect(() => {
    skipDoublonCheck.current = false;
    setDoublonData(null);
    setShowDoublonAlert(false);
  }, [formData.client_id]);

  const addLigne = () => {
    setFormData(prev => ({
      ...prev,
      lignes: [
        ...prev.lignes,
        {
          produit_id: '',
          quantite: 1,
          prix_unitaire: 0,
          remise_ligne: 0,
        }
      ]
    }));
  };

  const removeLigne = (index) => {
    setFormData(prev => ({
      ...prev,
      lignes: prev.lignes.filter((_, i) => i !== index)
    }));
  };

  const updateLigne = (index, field, value) => {
    setFormData(prev => {
      const newLignes = [...prev.lignes];
      newLignes[index][field] = value;

      // Auto-populate prix_unitaire when product is selected
      if (field === 'produit_id') {
        // Try both product_id (legacy) and reference (current)
        const produit = produits.find(p => p.product_id === value || p.reference === value);
        if (produit) {
          newLignes[index].prix_unitaire = produit.prix_vente;
        }
      }

      return { ...prev, lignes: newLignes };
    });
  };

  const calculateMontantLigne = (ligne) => {
    const base = ligne.quantite * ligne.prix_unitaire;
    return base * (1 - ligne.remise_ligne / 100);
  };

  const calculateTotals = () => {
    const montant_ht = formData.lignes.reduce((sum, ligne) => sum + calculateMontantLigne(ligne), 0);
    const montant_remise = montant_ht * (formData.remise_globale / 100);
    const montant_total = montant_ht - montant_remise;
    return { montant_ht, montant_remise, montant_total };
  };

  const validateStep = (stepNum) => {
    if (stepNum === 1) {
      if (!formData.client_id) {
        toast.error('Veuillez sélectionner un client');
        return false;
      }
    }
    if (stepNum === 2) {
      if (formData.lignes.length === 0) {
        toast.error('Veuillez ajouter au moins une ligne');
        return false;
      }
      for (const ligne of formData.lignes) {
        if (!ligne.produit_id || ligne.quantite <= 0 || ligne.prix_unitaire <= 0) {
          toast.error('Veuillez compléter toutes les lignes');
          return false;
        }
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep(step + 1);
    }
  };

  const handlePrev = () => {
    setStep(step - 1);
  };

  const handleSubmit = async (submit = false) => {
    if (!validateStep(2)) return;

    setLoading(true);
    try {
      // Map lignes to API format: API expects `product_id` (UUID). The UI stores the
      // product reference (ex: FABS-CI99) in `produit_id`, so resolve it to the real
      // product_id when the produit has one, else keep the value as-is.
      const payload = {
        ...formData,
        lignes: formData.lignes.map((ligne) => {
          const produit = produits.find(
            (p) => p.product_id === ligne.produit_id || p.reference === ligne.produit_id
          );
          return {
            product_id: produit?.product_id || ligne.produit_id,
            quantite: ligne.quantite,
            prix_unitaire: ligne.prix_unitaire,
            remise_ligne: ligne.remise_ligne || 0,
          };
        }),
      };
      let commande;
      if (isEdit) {
        commande = await updateCommande(editId, payload);
        toast.success('Commande modifiée avec succès');
        navigate(`/commandes/${editId}`);
      } else {
        commande = await createCommande(payload, submit);
        toast.success(submit ? 'Commande soumise avec succès' : 'Brouillon enregistré');
        navigate(`/commandes/${commande.commande_id}`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || (isEdit ? 'Erreur lors de la modification' : 'Erreur lors de la création'));
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount) + ' FCFA';
  };

  const totals = calculateTotals();

  // Handlers doublon
  const handleDoublonContinue = async () => {
    if (doublonData?.logId) {
      try { await logDoublonDecision(doublonData.logId, 'continuer'); } catch {}
    }
    skipDoublonCheck.current = true;
    setShowDoublonAlert(false);
  };

  const handleDoublonCancel = async () => {
    if (doublonData?.logId) {
      try { await logDoublonDecision(doublonData.logId, 'annuler'); } catch {}
    }
    navigate('/commandes');
  };

  return (
    <DashboardLayout>
    {/* Dialog doublon */}
    <DoublonAlert
      open={showDoublonAlert}
      commande={doublonData?.commande}
      niveau={doublonData?.niveau}
      logId={doublonData?.logId}
      onContinue={handleDoublonContinue}
      onCancel={handleDoublonCancel}
    />
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate('/commandes')}
          data-testid="btn-retour"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Retour
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-[#0A2540] dark:text-white">{isEdit ? 'Modifier la commande' : 'Nouvelle commande'}</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Étape {step} sur 3</p>
        </div>
      </div>

      {/* Steps Indicator */}
      <div className="flex items-center justify-center mb-8">
        {[1, 2, 3].map((s) => (
          <React.Fragment key={s}>
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                s <= step ? 'bg-[#FF6200] text-white' : 'bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-white/70'
              }`}
            >
              {s}
            </div>
            {s < 3 && (
              <div className={`h-1 w-24 ${s < step ? 'bg-[#FF6200]' : 'bg-gray-200 dark:bg-white/10'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: Select Client */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Sélection du client</CardTitle>
            <CardDescription>Recherchez un client existant ou créez-en un nouveau</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ClientPicker
              clients={clients}
              selectedClient={selectedClient}
              onSelect={handleClientSelect}
              onClientCreated={(c) => setClients((prev) => [c, ...prev])}
            />

            {selectedClient && (
              <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200">
                <CardContent className="pt-6">
                  <h4 className="font-semibold mb-2 text-[#0A2540] dark:text-blue-200">
                    ✓ Client sélectionné
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Nom :</span>{' '}
                      <span className="font-medium">{selectedClient.nom}</span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Type :</span>{' '}
                      <Badge>{selectedClient.type_client}</Badge>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Téléphone :</span>{' '}
                      {selectedClient.telephone || '-'}
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Ville :</span>{' '}
                      {selectedClient.ville || '-'}
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-600 dark:text-gray-400">Représentant :</span>{' '}
                      {selectedClient.representant || '-'}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="flex justify-end gap-2 mt-6">
              <Button onClick={handleNext} data-testid="btn-next-step1">
                Suivant <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Add Product Lines */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Lignes de commande</CardTitle>
            <CardDescription>Ajoutez les produits à commander</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={addLigne}
              variant="outline"
              className="w-full"
              data-testid="btn-add-ligne"
            >
              <Plus className="h-4 w-4 mr-2" />
              Ajouter une ligne
            </Button>

            {formData.lignes.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-white/50">
                Aucune ligne ajoutée. Cliquez sur "Ajouter une ligne" pour commencer.
              </div>
            ) : (
              <div className="space-y-4">
                {formData.lignes.map((ligne, index) => (
                  <Card key={index} className="bg-gray-50 dark:bg-gray-800">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start mb-4">
                        <h4 className="font-semibold">Ligne {index + 1}</h4>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeLigne(index)}
                          data-testid={`btn-remove-ligne-${index}`}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="col-span-2">
                          <Label>Produit *</Label>
                          <Popover
                            open={openProduitIdx === index}
                            onOpenChange={(o) => setOpenProduitIdx(o ? index : null)}
                          >
                            <PopoverTrigger asChild>
                              <Button
                                variant="outline"
                                className="w-full justify-between font-normal"
                                data-testid={`select-produit-${index}`}
                              >
                                <span className="truncate">
                                  {ligne.produit_id
                                    ? produits.find(p => p.product_id === ligne.produit_id || p.reference === ligne.produit_id)?.titre || 'Sélectionner'
                                    : 'Sélectionner un produit'}
                                </span>
                                <ChevronsUpDown className="h-4 w-4 opacity-50 shrink-0 ml-2" />
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-[400px] p-0" align="start">
                              <Command>
                                <CommandInput placeholder="Rechercher produit..." />
                                <CommandList>
                                  {loadingProduits ? (
                                    <div className="bg-blue-50 dark:bg-blue-950 p-4 text-center text-sm text-blue-600 dark:text-blue-300">
                                      <div className="flex items-center justify-center gap-2">
                                        <div className="h-2 w-2 bg-blue-500 rounded-full animate-bounce"></div>
                                        Chargement des produits...
                                      </div>
                                    </div>
                                  ) : produits.length === 0 ? (
                                    <div className="bg-amber-50 dark:bg-amber-950 p-4 text-center text-sm text-amber-600 dark:text-amber-300">
                                      Aucun produit trouvé
                                    </div>
                                  ) : (
                                    Array.isArray(produits) && produits.map((produit) => (
                                      <CommandItem
                                        key={produit.reference || produit.product_id}
                                        value={`${produit.titre} ${produit.reference}`}
                                        onSelect={() => {
                                          // Use reference as the unique key (FABS-CI79, etc.)
                                          updateLigne(index, 'produit_id', produit.reference || produit.product_id);
                                          setOpenProduitIdx(null);
                                        }}
                                      >
                                        <Check
                                          className={`mr-2 h-4 w-4 shrink-0 ${(ligne.produit_id === produit.reference || ligne.produit_id === produit.product_id) ? 'opacity-100' : 'opacity-0'}`}
                                        />
                                        <div>
                                          <div className="font-medium">{produit.titre}</div>
                                          <div className="text-xs text-gray-500 dark:text-white/50">
                                            {produit.reference} — {formatCurrency(produit.prix_vente)}
                                          </div>
                                        </div>
                                      </CommandItem>
                                    ))
                                  )}
                                </CommandList>
                              </Command>
                            </PopoverContent>
                          </Popover>
                        </div>

                        <div>
                          <Label>Quantité *</Label>
                          <Input
                            type="number"
                            min="1"
                            value={ligne.quantite}
                            onChange={(e) => updateLigne(index, 'quantite', parseInt(e.target.value) || 1)}
                            data-testid={`input-quantite-${index}`}
                          />
                        </div>

                        <div>
                          <Label>Prix unitaire *</Label>
                          <Input
                            type="number"
                            min="0"
                            step="100"
                            value={ligne.prix_unitaire}
                            onChange={(e) => updateLigne(index, 'prix_unitaire', parseFloat(e.target.value) || 0)}
                            data-testid={`input-prix-${index}`}
                          />
                        </div>

                        <div>
                          <Label>Remise ligne (%)</Label>
                          <Input
                            type="number"
                            min="0"
                            max="100"
                            step="0.01"
                            value={ligne.remise_ligne}
                            onChange={(e) => {
                              const v = e.target.value;
                              updateLigne(index, 'remise_ligne', v === '' ? 0 : parseFloat(v));
                            }}
                            data-testid={`input-remise-ligne-${index}`}
                          />
                        </div>

                        <div className="col-span-3 text-right">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Montant ligne:</span>{' '}
                          <span className="font-semibold text-lg">
                            {formatCurrency(calculateMontantLigne(ligne))}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            <div className="flex justify-between gap-2 mt-6">
              <Button variant="outline" onClick={handlePrev} data-testid="btn-prev-step2">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Précédent
              </Button>
              <Button onClick={handleNext} data-testid="btn-next-step2">
                Suivant <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Review & Submit */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Résumé et finalisation</CardTitle>
            <CardDescription>Vérifiez les informations avant de soumettre</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Client Info */}
            <div>
              <h4 className="font-semibold mb-2">Client</h4>
              <p className="text-gray-700 dark:text-gray-300">{selectedClient?.nom}</p>
              <p className="text-sm text-gray-500 dark:text-white/50">{selectedClient?.reference}</p>
            </div>

            <Separator />

            {/* Lines Summary */}
            <div>
              <h4 className="font-semibold mb-3">Lignes de commande</h4>
              <div className="space-y-2">
                {formData.lignes.map((ligne, index) => {
                  const produit = produits.find(p => p.product_id === ligne.produit_id || p.reference === ligne.produit_id);
                  return (
                    <div key={index} className="flex justify-between text-sm">
                      <span>
                        {produit?.titre} x {ligne.quantite}
                        {ligne.remise_ligne > 0 && (
                          <Badge variant="outline" className="ml-2">-{ligne.remise_ligne}%</Badge>
                        )}
                      </span>
                      <span className="font-medium">{formatCurrency(calculateMontantLigne(ligne))}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <Separator />

            {/* Additional Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="date_livraison">Date livraison prévue</Label>
                <Input
                  id="date_livraison"
                  type="date"
                  value={formData.date_livraison_prevue}
                  onChange={(e) => setFormData(prev => ({ ...prev, date_livraison_prevue: e.target.value }))}
                  data-testid="input-date-livraison"
                />
              </div>

              <div>
                <Label htmlFor="remise_globale">Remise globale (%)</Label>
                <Input
                  id="remise_globale"
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  value={formData.remise_globale}
                  onChange={(e) => {
                    const v = e.target.value;
                    setFormData(prev => ({ ...prev, remise_globale: v === '' ? 0 : parseFloat(v) }));
                  }}
                  data-testid="input-remise-globale"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                placeholder="Notes internes..."
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                data-testid="textarea-notes"
              />
            </div>

            <Separator />

            {/* Totals */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg space-y-2">
              <div className="flex justify-between text-sm">
                <span>Sous-total HT:</span>
                <span>{formatCurrency(totals.montant_ht)}</span>
              </div>
              {formData.remise_globale > 0 && (
                <div className="flex justify-between text-sm text-orange-600">
                  <span>Remise globale ({formData.remise_globale}%):</span>
                  <span>-{formatCurrency(totals.montant_remise)}</span>
                </div>
              )}
              <Separator />
              <div className="flex justify-between text-lg font-bold">
                <span>Total:</span>
                <span className="text-[#FF6200]">{formatCurrency(totals.montant_total)}</span>
              </div>
            </div>

            {totals.montant_total > 500000 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  ⚠️ Cette commande nécessite une validation du Directeur Général (montant &gt; 500 000 FCFA)
                </p>
              </div>
            )}

            <div className="flex justify-between gap-2 mt-6">
              <Button variant="outline" onClick={handlePrev} data-testid="btn-prev-step3">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Précédent
              </Button>
              <div className="flex gap-2">
                {isEdit ? (
                  <Button
                    onClick={() => handleSubmit(false)}
                    disabled={loading}
                    className="bg-[#FF6200] hover:bg-[#E55900]"
                    data-testid="btn-save-edit"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Enregistrer les modifications
                  </Button>
                ) : (
                  <>
                    <Button
                      variant="outline"
                      onClick={() => handleSubmit(false)}
                      disabled={loading}
                      data-testid="btn-save-draft"
                    >
                      <Save className="h-4 w-4 mr-2" />
                      Enregistrer brouillon
                    </Button>
                    <Button
                      onClick={() => handleSubmit(true)}
                      disabled={loading}
                      className="bg-[#FF6200] hover:bg-[#E55900]"
                      data-testid="btn-submit"
                    >
                      <Send className="h-4 w-4 mr-2" />
                      Soumettre
                    </Button>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </DashboardLayout>
  );
}
