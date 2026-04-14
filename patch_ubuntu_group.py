import xmlrpc.client
import datetime
import ssl

# --- Konfiguracja ---
MANAGER_URL = "https://your-suse-manager-server.local/rpc/api"
MANAGER_LOGIN = "your_username"
MANAGER_PASSWORD = "your_password"

# Dokladna nazwa grupy systemow w SUSE Manager
TARGET_GROUP_NAME = "Ubuntu_Servers" 

# Mozna ustawic False, jesli sa problemy z SSL ale to raczej jesli SUMA uzywa certyfikatu self-signed
VERIFY_SSL = True 
# ---------------------

def main():
    context = None
    if not VERIFY_SSL:
        context = ssl._create_unverified_context()
        
    client = xmlrpc.client.ServerProxy(MANAGER_URL, context=context)
    
    try:
        print(f"Logowanie do SUSE Manager pod adresem {MANAGER_URL}...")
        session = client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
        
        # 1. Pobierz systemy z podanej grupy
        print(f"Pobieranie systemow dla grupy: '{TARGET_GROUP_NAME}'...")
        try:
            systems_in_group = client.systemgroup.listSystemsMinimal(session, TARGET_GROUP_NAME)
        except xmlrpc.client.Fault as e:
            # Wylapywanie specyficznych bledow, np. literowka w nazwie grupy lub jej brak
            print(f"Blad podczas pobierania grupy: {e.faultCode} - {e.faultString}")
            return

        if not systems_in_group:
            print(f"Nie znaleziono systemow w grupie '{TARGET_GROUP_NAME}'. Konczenie.")
            return
            
        print(f"Znaleziono {len(systems_in_group)} system(ow) w grupie '{TARGET_GROUP_NAME}'.")
        
        # 2. Przejdz przez kazdy system i zastosuj latki
        for sys in systems_in_group:
            system_id = sys.get('id')
            system_name = sys.get('name', 'Unknown')
            
            print(f"\n--- Sprawdzanie systemu: {system_name} (ID: {system_id}) ---")
            
            # Pobierz odpowiednie erraty bezpieczenstwa
            errata_list = client.system.getRelevantErrataByType(session, system_id, "Security Advisory")
            
            if not errata_list:
                print(f"Nie znaleziono errat bezpieczenstwa dla {system_name}. System jest zaktualizowany!")
                continue
            
            # Wyciagnij id wymagane przez scheduleApplyErrata
            errata_ids = [erratum.get('id') for erratum in errata_list]
            
            print(f"Znaleziono {len(errata_ids)} errat bezpieczenstwa.")
            
            # Utworz obiekt DateTime dla XML-RPC
            now = xmlrpc.client.DateTime(datetime.datetime.now())
            
            # Dodaj zadanie patchowania
            action_id = client.system.scheduleApplyErrata(session, system_id, errata_ids, now)
            print(f"Pomyslnie zaplanowano patchowanie dla {system_name}. ID akcji: {action_id}")
            
    except xmlrpc.client.Fault as e:
        print(f"Blad XML-RPC: {e.faultCode} - {e.faultString}")
    except Exception as e:
        print(f"Wystapil nieoczekiwany blad: {e}")
    finally:
        # Zawsze czysc sesje po zakonczeniu
        if 'session' in locals():
            client.auth.logout(session)
            print("\nPomyslnie wylogowano.")

if __name__ == "__main__":
    main()
