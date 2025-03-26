workspace {
    name "Сервис поиска попутчиков"
    description "Приложение для организации совместных поездок."
 
    !identifiers hierarchical

    model {

        u1 = person "Пользователь"
        u2 = person "Администратор"

        s1  = softwareSystem "Картографический сервис"
        s2 = softwareSystem "Поиск попутчиков" {
            -> s1 "Расчет и подбор маршрутов"  

        webApp = container "Single Page Application" {
                technology "Python FastAPI React"
        }

        db = container "Database" {
                technology "PostgreSQL 17.4"
            }
        
        userService = container "UserService" {
                technology "Python FastAPI "
                -> db "сохранение и получение информации о пользователе" "sqlalchemy"
            }

        routeService = container "RouteService"{
            technology "Python FastAPI"
                -> db "сохранение и получение информации о маршруте" "sqlalchemy"
        }

        tripService = container "TripService"{
            technology "Python FastAPI"
                -> db "сохранение и получение информации о поездке" "sqlalchemy"
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
        routeService -> s1 "Расчет расстояния/определение путей"
     
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
            s2.tripService -> s2.db "UPDATE trips SET user_ids = array_append(user_ids, user_id) WHERE trip_id=request.trip_id"
            s2.tripService -> s2.be "возвращает подтверждение подключения"
            s2.be -> s2.webApp "отображение подтверждения подключения / STATUS CODE 200"
        }

    }

}