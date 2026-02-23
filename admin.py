#!/usr/bin/env python3
"""Script d'administration CLI pour gérer les clients Nexus Grid."""

import sys

from app.database import SessionLocal, init_db
from app.models import Client


def _get_db():
    return SessionLocal()


def add_client(name: str, credits: int = 0):
    """Créer un nouveau client avec une clé API générée automatiquement."""
    db = _get_db()
    api_key = Client.generate_api_key()
    client = Client(name=name, api_key=api_key, status="pending_payment", credits=credits)
    db.add(client)
    db.commit()
    db.refresh(client)
    print(f"Client créé :")
    print(f"  ID       : {client.id}")
    print(f"  Nom      : {client.name}")
    print(f"  API Key  : {client.api_key}")
    print(f"  Statut   : {client.status}")
    print(f"  Crédits  : {client.credits}")
    db.close()


def activate_client(client_id: int):
    """Activer un client après réception du virement."""
    db = _get_db()
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        print(f"Erreur : client #{client_id} introuvable.")
        db.close()
        return
    client.status = "active"
    db.commit()
    print(f"Client #{client.id} ({client.name}) activé.")
    db.close()


def add_credits(client_id: int, amount: int):
    """Ajouter des crédits à un client."""
    db = _get_db()
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        print(f"Erreur : client #{client_id} introuvable.")
        db.close()
        return
    client.credits += amount
    db.commit()
    print(f"Client #{client.id} ({client.name}) : {client.credits} crédits (ajout de {amount}).")
    db.close()


def list_clients():
    """Afficher tous les clients."""
    db = _get_db()
    clients = db.query(Client).all()
    if not clients:
        print("Aucun client enregistré.")
        db.close()
        return
    print(f"{'ID':<5} {'Nom':<25} {'Statut':<18} {'Crédits':<10} {'API Key'}")
    print("-" * 90)
    for c in clients:
        print(f"{c.id:<5} {c.name:<25} {c.status:<18} {c.credits:<10} {c.api_key}")
    db.close()


def print_usage():
    print("Usage : python admin.py <commande> [arguments]")
    print()
    print("Commandes :")
    print("  add <nom> [crédits]       — Créer un nouveau client")
    print("  activate <id>             — Activer un client (après virement)")
    print("  credits <id> <montant>    — Ajouter des crédits à un client")
    print("  list                      — Lister tous les clients")


def main():
    init_db()

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 3:
            print("Erreur : nom du client requis.")
            print("  python admin.py add <nom> [crédits]")
            sys.exit(1)
        name = sys.argv[2]
        credits = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        add_client(name, credits)

    elif command == "activate":
        if len(sys.argv) < 3:
            print("Erreur : ID du client requis.")
            sys.exit(1)
        activate_client(int(sys.argv[2]))

    elif command == "credits":
        if len(sys.argv) < 4:
            print("Erreur : ID et montant requis.")
            print("  python admin.py credits <id> <montant>")
            sys.exit(1)
        add_credits(int(sys.argv[2]), int(sys.argv[3]))

    elif command == "list":
        list_clients()

    else:
        print(f"Commande inconnue : {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
