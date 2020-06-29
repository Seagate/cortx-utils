# vault-dev

This Repository contains development environment vault config data.


#### Hashicorp Vault
Vault is an open-source tool used for securely storing and managing secrets. Here in RE we are storing SSH keys, Servers access credentials (username, passowrd) and other RE related secrets in the Vault 

**Benifits of using vault**
  - Vault is the single source of truth for all secrets.
  - Vault manages encryption (during transit and at rest) out of the box.
  - Secrets can be dynamically generated.
  - Secrets can be leased and revoked.
  - There's an audit trail for generating and using secrets.

**RE - Vault Configuration**  

| Vault Component | Use | RE Configuration | 
| ------ | ------ | ------ |
| Storage | Where secrets are stored | Filesystem |
| Secret | Handles static or dynamic secrets | SSH, Server Access Credentials |
| Auth | Handles authentication and authorization | Tokens, Username & Password |
| Audit | Logs all requests and responses | File |  

<br/>

**Directory Structure & Usage**   

``` bash
└── vault
    ├── config
    ├── data
    ├── init
    ├── logs
    └── policies
```
  - config : Contains vault initilization configurations like vault adderss, data path..etc
  - data : Acts as a persistent storage data when using the file data storage plugin 
  - init : Contains unseal key used to provision the vault.  
  - logs : Used for writing persistent audit logs. 
  - policies : This folder acts as a reference for all the access polices used in this vault. 


### Vault Deployment

**Prerequisites** 
  - Docker ( > 19.03)
  - Docker compose ( > 1.25)

**Setup** 

1. Clone this repository   
    ```
    git clone http://gitlab.mero.colo.seagate.com/736373/vault-dev.git
    cd vault-dev
    ```
2. Launch the vault server
   ```
    docker-compose up -d
   ```
   
3. Access vault
    - UI
   ```
     http://<server_ip>:8200/ui
   ```
    - CMD
   ```
     docker-compose exec vault bash
     vault login
   ```
