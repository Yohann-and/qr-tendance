import streamlit as st
import hashlib
import json
import os
from datetime import datetime

class AuthManager:
    def __init__(self):
        self.config_file = "auth_config.json"
        self.default_credentials = {
            "administrator": {
                "password": "RichyMLG007",
                "role": "admin",
                "created_at": datetime.now().isoformat()
            }
        }
        self.load_config()
    
    def load_config(self):
        """Charge la configuration d'authentification"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.credentials = json.load(f)
            else:
                self.credentials = self.default_credentials
                self.save_config()
        except Exception as e:
            st.error(f"Erreur de chargement de la configuration: {str(e)}")
            self.credentials = self.default_credentials
    
    def save_config(self):
        """Sauvegarde la configuration d'authentification"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.credentials, f, indent=2)
        except Exception as e:
            st.error(f"Erreur de sauvegarde de la configuration: {str(e)}")
    
    def hash_password(self, password):
        """Hache un mot de passe"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_credentials(self, username, password):
        """Vérifie les identifiants"""
        if username in self.credentials:
            stored_password = self.credentials[username]["password"]
            # Vérification directe (pour rétrocompatibilité)
            if stored_password == password:
                return True
            # Vérification avec hash
            elif stored_password == self.hash_password(password):
                return True
        return False
    
    def login(self):
        """Interface de connexion"""
        st.title("🔐 Connexion - Dashboard QR Pointage")
        
        # Affichage de l'image de connexion
        try:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("logo.jpeg", width=300, caption="Dashboard QR Pointage")
        except:
            pass  # Si l'image n'est pas trouvée, on continue sans
        
        st.markdown("---")
        
        with st.form("login_form"):
            st.markdown("### Veuillez vous connecter pour accéder au dashboard")
            
            username = st.text_input("Nom d'utilisateur", placeholder="administrator")
            password = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
            
            submitted = st.form_submit_button("Se connecter", use_container_width=True)
            
            if submitted:
                if self.verify_credentials(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = self.credentials[username]["role"]
                    st.success("Connexion réussie! Redirection...")
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect.")
                    st.info("Identifiants par défaut: administrator / RichyMLG007")
    
    def logout(self):
        """Déconnexion"""
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.rerun()
    
    def is_authenticated(self):
        """Vérifie si l'utilisateur est authentifié"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self):
        """Récupère l'utilisateur actuel"""
        return st.session_state.get('username', None)
    
    def change_password(self, username, old_password, new_password):
        """Change le mot de passe d'un utilisateur"""
        if self.verify_credentials(username, old_password):
            self.credentials[username]["password"] = new_password
            self.credentials[username]["updated_at"] = datetime.now().isoformat()
            self.save_config()
            return True
        return False
    
    def add_user(self, username, password, role="user"):
        """Ajoute un nouvel utilisateur"""
        if username not in self.credentials:
            self.credentials[username] = {
                "password": password,
                "role": role,
                "created_at": datetime.now().isoformat()
            }
            self.save_config()
            return True
        return False
    
    def delete_user(self, username):
        """Supprime un utilisateur"""
        if username in self.credentials and username != "administrator":
            del self.credentials[username]
            self.save_config()
            return True
        return False
    
    def get_users(self):
        """Récupère la liste des utilisateurs"""
        return list(self.credentials.keys())
    
    def show_user_management(self):
        """Interface de gestion des utilisateurs"""
        if not self.is_authenticated() or st.session_state.get('user_role') != 'admin':
            st.error("Accès refusé. Droits administrateur requis.")
            return
        
        st.subheader("👥 Gestion des Utilisateurs")
        
        # Changement de mot de passe
        with st.expander("🔑 Changer le mot de passe"):
            with st.form("change_password_form"):
                current_password = st.text_input("Mot de passe actuel", type="password")
                new_password = st.text_input("Nouveau mot de passe", type="password")
                confirm_password = st.text_input("Confirmer le nouveau mot de passe", type="password")
                
                if st.form_submit_button("Changer le mot de passe"):
                    if new_password != confirm_password:
                        st.error("Les mots de passe ne correspondent pas.")
                    elif len(new_password) < 6:
                        st.error("Le mot de passe doit contenir au moins 6 caractères.")
                    elif self.change_password(st.session_state.username, current_password, new_password):
                        st.success("Mot de passe modifié avec succès!")
                    else:
                        st.error("Mot de passe actuel incorrect.")
        
        # Ajout d'utilisateur
        with st.expander("➕ Ajouter un utilisateur"):
            with st.form("add_user_form"):
                new_username = st.text_input("Nom d'utilisateur")
                new_user_password = st.text_input("Mot de passe", type="password")
                new_user_role = st.selectbox("Rôle", ["user", "admin"])
                
                if st.form_submit_button("Ajouter l'utilisateur"):
                    if not new_username or not new_user_password:
                        st.error("Veuillez remplir tous les champs.")
                    elif self.add_user(new_username, new_user_password, new_user_role):
                        st.success(f"Utilisateur {new_username} ajouté avec succès!")
                    else:
                        st.error("Cet utilisateur existe déjà.")
        
        # Liste des utilisateurs
        with st.expander("📋 Utilisateurs existants"):
            users = self.get_users()
            for user in users:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{user}**")
                with col2:
                    st.write(f"Rôle: {self.credentials[user]['role']}")
                with col3:
                    if user != "administrator":
                        if st.button("🗑️", key=f"delete_{user}"):
                            if self.delete_user(user):
                                st.success(f"Utilisateur {user} supprimé.")
                                st.rerun()
    
    def show_auth_status(self):
        """Affiche le statut d'authentification dans la sidebar"""
        if self.is_authenticated():
            with st.sidebar:
                st.markdown("---")
                st.markdown(f"👤 **Connecté**: {st.session_state.username}")
                st.markdown(f"🎭 **Rôle**: {st.session_state.user_role}")
                
                if st.button("🚪 Déconnexion", use_container_width=True):
                    self.logout()
                
                if st.session_state.user_role == "admin":
                    st.markdown("---")
                    if st.button("⚙️ Paramètres", use_container_width=True):
                        st.session_state.show_settings = True
                        st.rerun()