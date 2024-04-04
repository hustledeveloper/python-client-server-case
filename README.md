# python server client application
 
### Kurulum

1. Repository'yi klonlayın:
   ```bash
   git clone https://github.com/hustledeveloper/python-client-server-case
   ```
2. Proje dizinine gidin:
   ```bash
   cd python-client-server-case
   ```
3. Docker Compose kullanarak MySQL veri tabanını oluşturun. Server buna bağlanıyor
   ```bash
   docker-compose up -d
4. Client sqlite kullanıyor localde

5. server.log ve client.log da loglar tutulmakta

6. client-id elle girilerek birden fazla client oluşturup thread kullanarak race conditiona girmeden çalışmaları sağlanmıştır

