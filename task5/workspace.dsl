workspace {
    name "Сервис поиска попутчиков"
    description "Приложение для организации совместных поездок."
 
    !identifiers hierarchical

    model {

        u1 = person "Пользователь"
        u2 = person "Администратор"

        s2 = softwareSystem "Поиск попутчиков" {

        webApp = container "Single Page Application" {
                technology "Python FastAPI React"
        }

        postgres_db = container "PostgreSQL" {
                technology "PostgreSQL 17.4"
            }

        mongo_db =  container "MongoDB" {
                technology "MongoDB 5.0"
            }
        
        fake_db = container "Fake DB"{
            technology "JSON"
        }

        redis = container "Redis" {
            technology "Redis"
        }

        userService = container "UserService" {
                userService -> redis "Система кеширования данных"
                redis -> postgres_db "сохранение и получение информации о пользователе" "sqlalchemy"
                technology "Python FastAPI "
            }

        routeService = container "RouteService"{
            technology "Python FastAPI"
                -> fake_db "сохранение и получение информации о маршруте" "sqlalchemy"
        }

        tripService = container "TripService"{
            technology "Python FastAPI"
                -> mongo_db "сохранение и получение информации о поездке" "sqlalchemy"
        }

        be = container "API Gateway" {
                be -> userService "поиск/удаление/создание пользователя" "http-requests"
                be -> routeService  "создание/удаление/получение маршрутов" "http-requests"
                be -> tripService "создание/удаление поездки, подключение к поездке пользователей" "http-requests"
        
                technology "Python FastAPI"

        }

          adminInterface = container "AdminInterface"{
            technology "Python FastAPI React"
                -> be "Управление базой данных" 
        }
        
        u1 -> webApp "Найти попутчика/Настроить аккаунт" 

        u2 -> adminInterface "Изменить параметры пользователей" 

        webApp -> be "Получение/изменение сущностей базы данных"
     
        }

    }

    views {

        themes default
        
        container s2 "uc01" "vertical" {
            include *
            autoLayout
        }

        systemContext s2 "uc02" "vetrical" {
            include *
            autoLayout
        }


        dynamic s2 "uc03" "Подключение пользователя к существующей поездке" {
            
            autoLayout lr

            u1 -> s2.webApp "Выбирает подходящую поездку"
            s2.webApp -> s2.be "PATCH /trips/{tripId}/join {userId}"
            s2.be -> s2.tripService "PATCH /trips/{tripId}/join {userId}"
            s2.tripService -> s2.mongo_db "UPDATE trips SET user_ids = array_append(user_ids, user_id) WHERE trip_id=request.trip_id"
            s2.tripService -> s2.be "возвращает подтверждение подключения"
            s2.be -> s2.webApp "отображение подтверждения подключения / STATUS CODE 200"
        }

    }

}