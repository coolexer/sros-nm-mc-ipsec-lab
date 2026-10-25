# Условия запуска и восстановление стенда

Документ дополняет [программу испытаний](TEST-PROGRAM-RU.md) и
[итоговые результаты](../RESULTS.md). Измерения относятся к compact-профилю SR-SIM 26.7.R2.

## Ресурсы и время

Измеренный стенд: WSL2, 12 логических CPU, 17,15 ГиБ RAM и 5 ГиБ swap; хост Intel i5-1245U,
32 ГиБ физической RAM. Во время испытаний хост должен оставаться активным. Ресурсы WSL
необходимо выделять с учётом остальных задач хоста; swap не заменяет запас физической памяти.

В compact у каждого SecGW один IOM и одна MS-ISA2. У каждой пары SecGW два участника
LACP LAG на одной network MDA. Этот профиль проверяет отказ порта/линии. Для отдельного
IOM/MDA failure domain предусмотрен [reference-профиль](../profiles/dual-iom.clab.yml)
с размещением участника B на IOM 2; опубликованные измерения относятся к compact.

Все четыре SR OS узла используют общий NTP `172.20.30.123` через management network.
Лабораторный chronyd имеет local stratum 10 и запускается с `-x`; он предоставляет общее
время от WSL, не изменяя часы хоста. В production используется согласованный внешний
источник времени. Проверка: `show system ntp all` и выбранный Clock Source на каждом узле.

## Подготовка pool HA перед T9

Подготовка выполняется отдельно от измеряемого отказа. Перед обслуживанием OA находится
на seg1 или seg2, все узлы согласовали Current Active и имеют nominal.

1. Остановить CPM/IOM компоненты обоих DA, оставив их netns helpers, core и eNB запущенными.
   Эта операция относится к offline-обслуживанию и может прервать текущий трафик.
2. Проверить не менее **10 ГиБ physical MemAvailable** перед выделением HA tables.
3. На seg3 отключить ISA, задать pool `high-availability tunnel-limit-32k` и сохранить config.
4. Холодно запустить CPM и IOM seg3. Для IOM установить cgroup ceiling 8 ГиБ RAM /
   9 ГиБ RAM+swap. Дождаться CLI, включить ISA, дождаться operational и сохранить config.
5. Наблюдать operational ISA 60 секунд. Затем запустить DA по очереди, проверяя CLI и
   forwarding-маршруты каждого узла.
6. Дождаться обеих IKE/CHILD SA, успешных readiness-проб, nominal и штатных маршрутов через seg1.
   SPI для T9 записываются после завершения подготовки.

Указанные значения являются условиями этой лаборатории, а не спецификацией аппаратной
ёмкости Nokia. Режим HA 32k задаёт ёмкость pool; в программе используются два IPsec-туннеля.
Подготовка реализована в `prepare_pool()` runner; фактический режим и состояние ISA
фиксируются в pool-preparation log заключительной группы.

## Возврат к обычному режиму

После T9r штатно вернуть OA на seg1 и выполнить обслуживание standby seg3:
отключить ISA, задать `high-availability none`, сохранить конфигурацию, перезапустить IOM,
включить ISA и сохранить её включённое состояние. После readiness-проб проверить nominal.
Трафик этих операций не входит в T9/T9r.

Core и eNB остаются запущенными в течение pool maintenance. Распределённые namespace
helpers SecGW также остаются запущенными, сохраняя data links между компонентами.

## Маршруты и shunting

Перед каждым плановым переключением на целевом SecGW проверяются BGP-маршруты к обеим
public eNB networks и private MME network. Проверка готовности включает forwarding routes,
SA и фактическую передачу трафика.

В T10–T12 core выбирает заданный standby с помощью neighbor import policy. Список policies
заменяется в одной MD-CLI candidate-транзакции: удалить прежний neighbor import, затем задать
нужный список и commit. Измерение начинается после проверки фактически выбранных next-hops.
После опыта neighbor overrides удаляются, и применяется штатная групповая policy.

BGP connect-retry равен 5 с; MRAI SecGW export groups — 1 с. BFD включён на core peerings,
кроме отдельного контрольного T7-noBFD. Согласованные BFD intervals проверяются через
`show router bfd session`; конфигурационное значение и фактическое время обнаружения
отказа должны рассматриваться отдельно.

## Финальная operational-проверка

Программа завершается со следующим состоянием:

- OA seg1; единый Current Active 10.0.0.1 и protection nominal на всех SecGW.
- Оба peer MCS DB Sync State — inSync на каждом SecGW.
- Обе IKE и CHILD SA установлены; на OA два installed tunnels.
- Gateway /32 и оба private /32 направлены core через seg1.
- Все SecGW имеют маршруты к обеим eNB networks и MME network.
- ISA operational; каждый LAG имеет два up-members.
- Shunting profiles восстановлены, route pinning снят, BFD включён, revertive false.
- Pool mode none; NTP выбран на всех четырёх SR OS узлах.
- Конфигурация сохранена на всех маршрутизаторах.

Исходный протокол проверки опубликован в [operational.log](../results/validated-final-state/operational.log).

## Документация Nokia

- [N:M MC-IPsec, pool HA, election и shunting](https://documentation.nokia.com/sr/26-7/7750-sr/books/ms-isa-esa/ip-tunnels.html).
- [SR-SIM и совместное использование ресурсов хоста](https://documentation.nokia.com/sr/26-7/7x50-shared/srsim-installation-setup/sr-sim-overview.html).
- [Требования к хосту SR-SIM](https://documentation.nokia.com/sr/26-7/7x50-shared/srsim-installation-setup/host-machine-requirements.html).
