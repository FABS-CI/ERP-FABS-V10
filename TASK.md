# TASK: Add Niveau & Matière to All Documents

## Status: NEARLY COMPLETE ✅

### What's Done
1. ✅ **Backend PDF** - Already enriches lignes with matiere + niveau via `enrich_lignes_for_pdf()`
2. ✅ **Backend API Models** - LigneCommandeOut & LigneFactureOut already have `produit_matiere` and `produit_niveau_scolaire`
3. ✅ **Backend API Routes** - GET commande/{id} and GET facture/{id} already call enrichment functions
4. ✅ **Frontend - ProduitDetail** - Already displays Matière + Niveau Scolaire
5. ✅ **Frontend - CommandeDetail** - JUST UPDATED: Replaced lignes list with LignesTable component that shows Niveau + Matière
6. ✅ **Frontend - FactureDetail** - JUST UPDATED: Replaced lignes list with LignesTable component that shows Niveau + Matière
7. ✅ **New Component** - Created `/frontend/src/components/document/LignesTable.jsx` - reusable table with proper columns

### Current Task
- Testing the implementation with real data
- Created test product: prod_b7ab1cd3bb19 with matiere="Français", niveau_scolaire="CP1"
- Need to create test commande with this product and verify frontend displays correctly

### Files Modified
- `/home/user/ERP-FABS-V10/frontend/src/pages/CommandeDetail.jsx` - Added LignesTable import + replaced lignes display
- `/home/user/ERP-FABS-V10/frontend/src/pages/FactureDetail.jsx` - Added LignesTable import + replaced lignes display
- `/home/user/ERP-FABS-V10/frontend/src/components/document/LignesTable.jsx` - NEW COMPONENT

### What Still Needs Testing
1. Browser test: Navigate to a commande with products that have matiere/niveau - should show in table ✅ TABLE READY
2. Browser test: Check facture detail - should show niveau/matière ✅ TABLE READY
3. Browser test: Generate PDF - should include Niveau + Matière columns ✅ BACKEND READY
4. Quick validation: Check fields are coming from API correctly

### Notes
- All 56 seed products don't have matiere/niveau populated - created one for testing
- PDF templates in pdf_generator.py ALREADY include Niveau/Matière in HDR_PRIX and HDR_NOPX
- The enrich_lignes_for_pdf() is already called before PDF generation in all modules
