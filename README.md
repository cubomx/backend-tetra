# Backend Tetra
## Requisites:
- Docker Desktop
- WSL
- Python3, Pip3
- Postman (test requests)

## Setup
1. Enable virtualization in your PC Bios.
2. Install WSL 2: `wsl install`
3. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
4. Run MongoDB:
    - Go to **/mongo**
    - Run `docker-compose up -d`
5. Run DJango app:
    - Go to **/** of the project  
    - Run `pip3 install Django==4.2 pandas pymongo openpyxl`

**NOTE**: Please, run all this at the Ubuntu terminal with the [Windows Terminal](https://apps.microsoft.com/detail/9n0dx20hk701)

The app is going to be running on port 8000.

## API Endpoints
- `/agenda/addEvento`
    - JSON: 
        - **name** : *str*
        - **type** : *str*
        - **day** : *int*
        - **month**: *int*
        - **year**: *int*
        - **location**: *str*
        - **num_of_people**: *int*
        - **cost**: *float*
        - **upfront**: *float*
- `/agenda/getEvento`
    - JSON: 
        - **name** : *str*
        - **type** : *str*
        - **day** : *int*
        - **month**: *int*
        - **year**: *int*
        - **location**: *str*
        - **num_of_people**: *int*
        - **cost**: *float*
        - **upfront**: *float*
    or simplely by sending **id_event**: *str*
- `/agenda/verAgenda`
    - JSON:  
        - **day** : *int*
        - **month**: *int*
        - **year**: *int*    
        - **isFuture**: *bool* (future is inclusive)
- `/agenda/delEvento`
    - JSON: 
        - **id_event**: *str*
- `/agenda/modifyEvento`
    - JSON (if you are going to change location/date) you must send all 4: 
        - **day** : *int*
        - **month**: *int*
        - **year**: *int*
        - **location**: *str*
    - JSON (other variables to update):
        - **name** : *str*
        - **type** : *str*
        - **num_of_people**: *int*
        - **cost**: *float*
        - **upfront**: *float*
- `/finanzas/addAbono`
    - JSON:
        - **id_event**: *str*
        - **payer**: *str*
        - **quantity**: *float* 
- `/finanzas/getAbono`
    - JSON:
        - **id_event**: *str*
        - **id_ticket**: *str*
    - JSON (you can use any combination of this filters):
        - **type** : *str* 
        - **day** : *int*
        - **month**: *int*
- `/finanzas/delAbono`
    - JSON:
        - **id_ticket**: *str*
- `/finanzas/addGasto`
    - JSON:
        - **id_event**: *str*
        - **day** : *int*
        - **month**: *int*
        - **year**: *int*
        - **location**: *str*
        - **concept**: *str*
        - **amount**: *int*
        - **category**: *str*
        - **expense_type**: *str*
        - **buyer**: *str*
        - **quantity**: *int*
- `/finanzas/getGasto`
    - JSON (any combination of filters):
        - **filters**: dict
            - **day** : *int*
            - **month**: *int*
            - **year**: *int*
            - **category**: *str*
            - **expense_type**: *str*
    - JSON (get expenses for a specific event)
        - **expenses**: dict
            - **id_event**: *str* 
- `/finanzas/modifyGasto`
    - JSON:
        - **id_event**: *str* 
        - **id_expense**: *str* 
        - **portion**: *float*
- `login`
    - JSON:
        - **email**: *str*
        - **password**: *str*
- `register`
    - JSON:
        - **name**: *str*
        - **password**: *str*
        - **email**: *str*
        - **role**: *str* (admin, finance, secretary, inventary)
    - Headers:
        - **Bearer Token**