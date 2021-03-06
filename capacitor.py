import math
import steam_water_func as swc


def capacitor(g_steam, p_steam, p_n, p_k, t_h, p_sk,
              tp=540, t_air=20, pr_air=0.703, v_air=15.06 * 10 ** (-6),
              e_d=0.9, kpd_t=0.95, lambd_d=50, d1=0.024, d2=0.026,
              lz=7.5, d=3.5, ny=75.86, nx=75.86, nsum =6000 - 246,
              lamb_air=0.0259, ns=8000):
    f_d = 3.14 * (d + 2 * ((d2 - d1) / 2)) * lz
    s_cw = 3.14 * d1 ** 2 * nsum / 4
    S_pipe = (d - d2 * nx) * lz
    h_tur = swc.superheated_steam_enthalpy(p_steam / 10, tp + 273) * 1000  # удельная энтальпия
    s_tur = swc.superheated_steam_entropy(p_steam / 10, tp + 273) * 1000  # удельная энтропия
    t_s = swc.satu_temp_by_satur_pressure(p_sk / 10) - 273  # температура в области наcыщения
    # параметры для кипящей воды
    h1 = swc.boiling_water_enthalpy(p_sk/10) * 1000
    s1 = swc.spec_entropy_of_subcooled_water(p_sk/10, t_s + 273) * 1000  # (энтропия кипящей воды)
    v1 = swc.volume_of_subcooled_liquid(p_sk/10, t_s + 273)
    # параметры сухого насыщенного пара
    h2 = swc.enthalpy_of_boiling_water_of_dr_saturated_steam(p_sk/10) * 1000
    s2 = swc.superheated_steam_entropy(p_sk/10, t_s + 273) * 1000
    v2 = swc.superheated_steam_volume(p_sk/10, t_s + 273)
    # параметры идеального обратимого расширения в турбине:
    x1 = (s_tur - s1) / (s2 - s1)
    h_s = h1 + x1 * (h2 - h1)
    # параметры расширения с учетом внутреннего относительного КПД турбины
    h_steam = h_tur - kpd_t * (h_tur - h_s)
    x_r = (h_steam - h1) / (h2 - h1)
    ro_steam = 1 / (v1 + x_r * (v2 - v1))
    # Используя введенные параметры определяется GХВ (g_vod)
    dp = p_n - p_k
    beta3 = 7 * 10 ** (-5) * t_h ** 2 - 0.0107 * t_h + 1.2209
    v_cv = -6.2532 * dp ** 2 + 11.014 * dp + 0.9291
    ro_hv = -0.0028 * t_h ** 2 - 0.1521 * t_h + 1002.3

    g_vod = ro_hv * beta3 * v_cv

    # оценка тепловых потерь конденсатора через корпус конденсатора в окружающую среду
    t_d = t_s - 1  # температура поверхности корпуса
    q_l = e_d * 5.67 * (((t_d + 273) / 100) ** 4 - ((t_air + 273) / 100) ** 4)
    alpha_d = (0.5 * lamb_air / d) * ((9.8 * (t_d - t_air) * d ** 3) / ((t_air + 273) * v_air ** 2) * pr_air) ** 0.25

    q_k = alpha_d * (t_d - t_air)  # лучистая составляющая теплового потока
    q_d = f_d * (q_l + q_k)  # тепловые потери конденсатора в окружающую среду
    w_steam = g_steam / (ro_steam * S_pipe)  # средняя скорость движения пара по конденсатору

    # Блок «Расчет начальных значений для итерационных циклов определения температуры стенки трубок,
    # температуры охлаждающей воды на выходе из конденсатора и массы сконденсированного пара

    c_p_cw = 0.0106 * t_h ** 2 - 0.8678 * t_h + 4197.1
    t_k_cw = t_h + g_steam * (h2 - h1) * 0.98 / (c_p_cw * g_vod)  # температура охл воды на выходе из конденсатора
    if t_k_cw > t_s:
        t_k_cw = t_s - 0.3
    # температуры стенок труб пучков по средней температуре охлаждающей воды
    t_cw = (t_h + t_k_cw) / 2
    t_st1 = (t_s + t_h) / 2 - 0.5
    t_st2 = (t_s + t_h) / 2 + 0.5
    g_con = x_r * g_steam  # приближение для сконденсированного в теплообменники пара
    gc_count = 0.01 * g_con

    # Блок «Расчет теплопередачи с заданными параметрами и оценка невязки по определению температуры стенки ΔtСТ2»

    while True:  # остановка цикла будет вручную в конце при помощи break.
        t_cw = (t_h + t_k_cw) / 2
        beta3 = 7 * 10 ** (-5) * t_cw ** 2 - 0.0107 * t_h + 1.2209
        g_vod = ro_hv * beta3 * v_cv
        # число (критерий) Прандтля,
        # а по температуре   только число (критерий) Прандтля
        lambd = -8 * 10 ** (-6) * t_cw ** 2 + 0.0019 * t_cw + 0.5634  # коэффициент теплопроводности,
        mu = (-9 * 10 ** (-7) * t_cw ** 3 + 3 * 10 ** (
            -4) * t_cw ** 2 - 0.0333 * t_cw + 1.5816) / 1000  # коэффициент динамической вязкости
        ro_hv = -0.0028 * t_cw ** 2 - 0.1521 * t_cw + 1002.3  # плотность
        pr_cw = -3 * 10 ** (-12) * t_cw ** 6 + 2 * 10 ** (-9) * t_cw ** 5 - 5 * 10 ** (-7) * t_cw ** 4 + 6 * 10 ** (
            -5) * t_cw ** 3 - 0.0019 * t_cw ** 2 - 0.1088 * t_cw + 9.3319
        pr_st1 = -3 * 10 ** (-12) * t_st1 ** 6 + 2 * 10 ** (-9) * t_st1 ** 5 - 5 * 10 ** (-7) * t_st1 ** 4 + 6 * 10 ** (
            -5) * t_st1 ** 3 - 0.0019 * t_st1 ** 2 - 0.1088 * t_st1 + 9.3319

        w_cw = g_vod / (ro_hv * s_cw)  # средняя скорость движения охлаждающей воды по трубам

        dt = ((t_s - t_h) - (t_s - t_k_cw)) / math.log((t_s - t_h) / (t_s - t_k_cw))  # среднелогарифмический температурный напор

        re = w_cw * d1 * ro_hv / mu
        if re > 10000 and (lz / d1) > 50:
            nu = 0.021 * re ** 0.8 * pr_cw ** 0.43 * (pr_cw / pr_st1) ** 0.25
            alpha_cw = nu * lambd / d1
        else:
            print("Напишите функцию для расчета ламинарного режима")
            break
        # определение параметров теплообмена при конденсации пара на поверхностях труб
        lambd_co = -8 * 10 ** (-6) * t_s ** 2 + 0.0019 * t_s + 0.5634  # коэффициент теплопроводности,
        mu_co = (-9 * 10 ** (-7) * t_s ** 3 + 3 * 10 ** (
            -4) * t_s ** 2 - 0.0333 * t_s + 1.5816) / 1000  # коэффициент динамической вязкости
        ro_co = -0.0028 * t_s ** 2 - 0.1521 * t_s + 1002.3  # плотность
        pr_co = -3 * 10 ** (-12) * t_s ** 6 + 2 * 10 ** (-9) * t_s ** 5 - 5 * 10 ** (-7) * t_s ** 4 + 6 * 10 ** (
            -5) * t_s ** 3 - 0.0019 * t_s ** 2 - 0.1088 * t_s + 9.3319
        alpha_n = 0.725 * (lambd_co ** 3 * 9.8 * (ro_co - ro_steam) * (h_steam - h1) / (
                    mu_co / ro_co * (t_s - t_st2) * d2)) ** 0.25
        if (ro_steam * w_steam ** 2) >= 1:
            a = 25.7 * (ro_steam * w_steam ** 2 / (9.8 * ro_co * d2)) ** 0.25 * (alpha_n * d2 / lambd_co) ** (-0.5)
        else:
            a = 1
        n_rows_h = ny
        b = 0.84 * (g_con / g_steam) / ((1 - (1 - g_con / g_steam) ** 0.84) * n_rows_h ** 0.07)

        alpha_con = alpha_cw * a * b  # Средний по всему трубному пучку коэффициент теплоотдачи при конденсации
        ql = 3.14 * dt / (1 / (alpha_cw * d1) + (1 / (2 * lambd_d)) * math.log(d2 / d1) + 1 / (alpha_con * d2))
        t_st2_new = t_s - ql / (3.14 * alpha_con * d2)
        #t_st1_new = t_st2_new - ql / (2 * 3.14 * lambd_d) * math.log(d2 / d1)

        dt_st2 = abs(t_st2_new - t_st2)

        # Анализ сходимости итерации

        if dt_st2 > 0.1:
            t_st2 = (t_st2 + t_st2_new) / 2
            continue  # возврат в начало цикла

        # Блок «Определение невязки по температуре охлаждающей воды на выходе из конденсатора

        c_p_cw = 0.0106 * t_cw ** 2 - 0.8678 * t_cw + 4197.1
        t_k_cw_new = t_h + (ql * lz * 2 * ns) / (c_p_cw * g_vod)
        dt_cw = abs(t_k_cw_new - t_k_cw)
        if dt_cw > 1:
            t_k_cw = (t_k_cw + t_k_cw_new) / 2
            continue

            # Блок «Определение невязки по массе сконденсированного пара ΔGКОН» ИЗМЕНЕНИЯ
        Gc_new = (ql * lz * 2 * ns) / (h_steam - h1)
        if Gc_new > x_r * g_steam:
            Gc_new = x_r * g_steam

        dGc = abs(Gc_new - g_con)
        if dGc > gc_count:
            g_con = (g_con + Gc_new) / 2
            continue
        else:
            break
    return g_vod


tes = capacitor(g_steam = 69 * 0.45, p_n=0.72, p_k=0.51, t_h=20, p_sk=0.03, p_steam=130)
print(tes)

