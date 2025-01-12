"""
Кобзарь О.С. Водопьян А.О. Хабибуллин Р.А. 10.08.2019

Новая BlackOil модель для расчета PVT свойств вместе с настройкой выбора методов, вынесенной отдельно.
"""
# TODO сделать калибровку параметров
# TODO сделать стандарт для функций, параметров и обозначений

import uniflocpy.uTools.uconst as uc
import uniflocpy.uPVT.PVT_correlations as PVT


class BlackOil_option():
    """
    Класс-пресет для настройки расчета моделей BlackOil. Данная структура хранит выбор методов, которые будут в расчете,
    для каждого параметра. При этом выбор корреляций и методов не влияет на поток данных при расчете.
    Также новые корреляции могут легко быть добавлены в модель BlackOil при расширении функций-контейнеров,
    через которые идет обращение к исходным функциям в PVT_correlations.

    По умолчанию настройка соответствует модели Стендинга
    """
    def __init__(self):
        # выбранные корреляции для нефти
        self.pb_cor_number = 0
        self.rs_cor_number = 0
        self.compr_oil_cor_number = 0
        self.b_oil_in_pb_cor_number = 0
        self.b_oil_below_pb_cor_number = 0
        self.b_oil_above_pb_cor_number = 0
        self.rho_oil_cor_number = 0
        self.mu_dead_oil_cor_number = 0
        self.mu_oil_pb_cor_number = 0
        self.mu_oil_any_p_cor_number = 0
        self.heatcap_oil_cor_number = 0
        self.thermal_conduct_oil_cor_number = 0

        # выбранные корреляции для газа
        self.pseudocritical_temperature_cor_number = 0
        self.pseudocritical_pressure_cor_number = 0
        self.z_cor_number = 0
        self.mu_gas_cor_number = 0
        self.b_gas_cor_number = 0
        self.compr_gas_cor_number = 0
        self.rho_gas_cor_number = 0
        self.heatcap_gas_cor_number = 0
        self.thermal_conduct_gas_cor_number = 0

        # выбранные корреляции для воды
        self.rho_wat_cor_number = 0
        self.compr_wat_cor_number = 0
        self.b_wat_cor_number = 0
        self.mu_wat_cor_number = 0
        self.rs_wat_cor_number = 0
        self.heatcap_wat_cor_number = 0
        self.thermal_conduct_wat_cor_number = 0
        self.thermal_expansion_wat_cor_number = 0
        self.sigma_oil_gas_cor_number = 0
        self.sigma_wat_gas_cor_number = 0

#  TODO передавать свойства нефти через структуру


class Fluid:
    def __init__(self, gamma_oil=0.86, gamma_gas=0.6, gamma_wat=1.0, rsb_m3m3=200.0, gamma_gassep=0, y_h2s=0, y_co2=0,
                 y_n2=0, s_ppm=0, par_wat=0, pb_cal_bar=-1., tpb_c=80, b_oil_b_cal_m3m3=0, mu_oil_b_cal_cp=0.5,
                 option=BlackOil_option()):
        """
        Cоздает флюид с заданными базовыми свойствами и определенным набором методик/корреляций для расчета

        калибровочные параметры при необходимости надо задавать отдельно

        :param gamma_oil: specific gravity of oil
        :param gamma_gas: specific gravity of gas (by air), dimensionless
        :param gamma_wat: specific gravity of water
        :param rsb_m3m3: solution gas ratio at bubble point
        :param gamma_gassep: specific gas density in separator(by air)
        :param y_h2s: mole fraction of the hydrogen sulfide
        :param y_co2: mole fraction of the carbon dioxide
        :param y_n2: mole fraction of the nitrogen
        :param s_ppm: water salinity
        :param par_wat: 0 = pure water, 1 = brine , 2 = brine with dissolved methane
        :param pb_cal_bar: давление насыщения, калибровочный параметр
        :param tpb_c: температура при давлении насыщения, калибровочный параметр
        :param b_oil_b_cal_m3m3: объемный коэффициент при давлении насыщения, калибровочный параметр
        :param mu_oil_b_cal_cp: вязкость при давлении насыщения, калибровочный параметр
        :param option: настройка расчета для выбора методик/корреляций, по умолчанию Стендинга
        """
        # опции расчета  # TODO понять, как разделить исходные данные и рассчитанные, может через структуру
        self.option = option
        # исходные данные
        self.gamma_gas = gamma_gas
        self.gamma_oil = gamma_oil
        self.gamma_wat = gamma_wat
        self.rsb_m3m3 = rsb_m3m3
        self.gamma_gassep = gamma_gassep
        self.y_h2s = y_h2s
        self.y_co2 = y_co2
        self.y_n2 = y_n2
        self.s_ppm = s_ppm
        self.par_wat = par_wat
        self.rho_oil_stkgm3 = gamma_oil * uc.rho_w_kgm3_sc  # TODO check?
        # термобарические условия
        self.p_bar = uc.psc_bar                 # thermobaric conditions for all parameters
        self.t_c = uc.tsc_c                     # can be set up by calc method
        # калибровочные параметры
        self.pb_cal_bar = pb_cal_bar
        self.tpb_C = tpb_c   # TODO разобраться с температурой насыщения
        self.b_oil_b_cal_m3m3 = b_oil_b_cal_m3m3
        self.mu_oil_b_cal_cp = mu_oil_b_cal_cp
        # расчетные параметры
        self.pb_bar = 0.0
        self.b_oil_b_m3m3 = 0.0
        self.mu_oil_b_cP = 0.0
        self.tpb_C = 0.0
        self.mu_oil_cp = 0.0        # TODO хорошо бы везде сделать единообразные индексы для нефти или o или oil 10.08. c oil и маленькими буквами
        self.mu_gas_cp = 0.0
        self.mu_wat_cp = 0.0
        self.mu_dead_oil_cp = 0.0
        self.rho_oil_kgm3 = 0.0
        self.rho_gas_kgm3 = 0.0
        self.rho_wat_kgm3 = 0.0
        self.rs_m3m3 = 0.0
        self.rsw_m3m3 = 0.0   # TODO проверить - равен GWR?
        self.b_oil_m3m3 = 0.0
        self.b_gas_m3m3 = 0.0
        self.b_wat_m3m3 = 0.0
        self.z = 0.0
        self.compr_oil_1bar = 0.0
        self.compr_oil_1mpa = 0.0
        self.compr_gas_1bar = 0.0
        self.compr_wat_1bar = 0.0
        self.heatcap_oil_jkgc = 0.0
        self.heatcap_gas_jkgc = 0.0
        self.heatcap_wat_jkgc = 0.0
        self.sigma_oil_gas_Nm = 0.0
        self.sigma_wat_gas_Nm = 0.0
        self.thermal_conduct_oil_wmk = 0.0
        self.thermal_conduct_gas_wmk = 0.0
        self.thermal_conduct_wat_wmk = 0.0
        self.thermal_expansion_wat_1c = 0.0
        # дополнительные расчетные параметры
        self.p_mpa = 0.0
        self.t_k = 0.0
        self.tpc_k = 0.0
        self.ppc_mpa = 0.0
        self.pb_mpa = 0.0

    def _calc_pb_MPaa(self, number_cor): # TODO калибровку свойств делать внутри функций контейнеров, чтобы оставался выбор корреляций
        if number_cor == 0:
            return PVT.unf_pb_Standing_MPaa(self.rsb_m3m3, self.gamma_oil, self.gamma_gas, self.t_k)
        if number_cor == 1:
            return PVT.unf_pb_Valko_MPaa(self.rsb_m3m3, self.gamma_oil, self.gamma_gas, self.t_k)
        if number_cor == 2:  # TODO check cor
            return PVT.unf_pb_Glaso_MPaa(self.rsb_m3m3, self.t_k, self.gamma_oil, self.gamma_gas)

    def _calc_rs_m3m3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_rs_Standing_m3m3(self.p_mpa, self.pb_mpa, self.rsb_m3m3, self.gamma_oil,
                                            self.gamma_gas, self.t_k)
        if number_cor == 1:
            return PVT.unf_rs_Velarde_m3m3(self.p_mpa, self.pb_mpa, self.gamma_oil,
                                           self.gamma_gas, self.t_k)

    def _calc_compr_oil_1mpa(self, number_cor):
        if number_cor == 0:
            return PVT.unf_compressibility_oil_VB_1Mpa(self.rs_m3m3, self.t_k, self.gamma_oil,
                                                       self.p_mpa, self.gamma_gas)

    def _calc_b_oil_in_pb_m3m3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_fvf_Standing_m3m3_saturated(self.rsb_m3m3, self.gamma_gas, self.gamma_oil, self.t_k)

    def _calc_b_oil_above_pb_m3m3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_fvf_VB_m3m3_above(self.b_oil_b_m3m3, self.compr_oil_1mpa,
                                             self.pb_mpa, self.p_mpa)

    def _calc_b_oil_below_pb_m3m3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_fvf_Standing_m3m3_saturated(self.rs_m3m3, self.gamma_gas, self.gamma_oil, self.t_k)
        if number_cor == 1:
            return PVT.unf_fvf_Glaso_m3m3_below(self.rs_m3m3, self.t_k, self.gamma_gas, self.gamma_oil, self.p_mpa)
        if number_cor == 2:
            return PVT.unf_fvf_Mccain_m3m3_below(self.rho_oil_stkgm3, self.rs_m3m3, self.rho_oil_kgm3,
                                                 self.gamma_gas)

    def _calc_rho_oil_kgm3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_density_oil_Standing(self.p_mpa, self.pb_mpa, self.compr_oil_1mpa, self.rs_m3m3,
                                                self.b_oil_m3m3, self.gamma_gas, self.gamma_oil)
        if number_cor == 1:
            return PVT.unf_density_oil_Mccain(self.p_mpa, self.pb_mpa, self.compr_oil_1mpa, self.rs_m3m3,
                                              self.gamma_gas, self.t_k, self.gamma_oil, self.gamma_gassep)

    def _calc_mu_dead_oil_cp(self, number_cor):
        if number_cor == 0:
            return PVT.unf_deadoilviscosity_Beggs_cP(self.gamma_oil, self.t_k)

    def _calc_mu_oil_in_pb_cp(self, number_cor):
        if number_cor == 0:
            return PVT.unf_saturatedoilviscosity_Beggs_cP(self.mu_dead_oil_cp, self.rsb_m3m3)

    def _calc_mu_oil_any_p_cp(self, number_cor):
        if number_cor == 0:
            return PVT.unf_oil_viscosity_Beggs_VB_cP(self.mu_dead_oil_cp, self.rs_m3m3,
                                                     self.p_mpa, self.pb_mpa)

    def _calc_heatcap_oil_jkgc(self, number_cor):
        if number_cor == 0:
            return PVT.unf_heat_capacity_oil_Gambill_JkgC(self.gamma_oil, self.t_c)
        if number_cor == 1:
            return PVT.unf_heat_capacity_oil_Wes_Wright_JkgC(self.gamma_oil, self.t_c)

    def _calc_thermal_conduct_oil_wmk(self, number_cor):
        if number_cor == 0:
            return PVT.unf_thermal_conductivity_oil_Cragoe_WmK(self.gamma_oil, self.t_c)
        if number_cor == 1:
            return PVT.unf_thermal_conductivity_oil_Abdul_Seoud_Moharam_WmK(self.gamma_oil, self.t_c)
        if number_cor == 2:
            return PVT.unf_thermal_conductivity_oil_Smith_WmK(self.gamma_oil, self.t_c)

    def _calc_pseudocritical_temperature_k(self, number_cor):
        if number_cor == 0:
            return PVT.unf_pseudocritical_temperature_K(self.gamma_gas, self.y_h2s, self.y_co2, self.y_n2)

    def _calc_pseudocritical_pressure_mpa(self, number_cor):
        if number_cor == 0:
            return PVT.unf_pseudocritical_pressure_MPa(self.gamma_gas, self.y_h2s, self.y_co2, self.y_n2)

    def _calc_zfactor(self, number_cor):
        if number_cor == 0:
            return PVT.unf_zfactor_DAK(self.p_mpa, self.t_k, self.ppc_mpa, self.tpc_k)

    def _calc_mu_gas_cp(self, number_cor):
        if number_cor == 0:
            return PVT.unf_gasviscosity_Lee_cP(self.t_k, self.p_mpa, self.z, self.gamma_gas)

    def _calc_b_gas_m3m3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_gas_fvf_m3m3(self.t_k, self.p_mpa, self.z)

    def _calc_compr_gas_1bar(self, number_cor):
        if number_cor == 0:
            return uc.compr_1mpa_2_1bar(PVT.unf_compressibility_gas_Mattar_1MPa(self.p_mpa, self.t_k,
                                                                                self.ppc_mpa, self.tpc_k))

    def _calc_rho_gas_kgm3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_gas_density_kgm3(self.t_k, self.p_mpa, self.gamma_gas, self.z)

    def _calc_heatcap_gas_jkgc(self, number_cor):
        if number_cor == 0:
            return PVT.unf_heat_capacity_gas_Mahmood_Moshfeghian_JkgC(self.p_mpa, self.t_k,
                                                                      self.gamma_gas)

    def _calc_thermal_conduct_gas_wmk(self, number_cor):
        if number_cor == 0:
            return PVT.unf_thermal_conductivity_gas_methane_WmK(self.t_c)

    def _calc_rho_wat_kgm3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_density_brine_Spivey_kgm3(self.t_k, self.p_mpa, self.s_ppm, self.par_wat)

    def _calc_compr_wat_1bar(self, number_cor):
        if number_cor == 0:
            return uc.compr_1mpa_2_1bar(PVT.unf_compressibility_brine_Spivey_1MPa(self.t_k, self.p_mpa, self.s_ppm,
                                                                                  self.z, self.par_wat))

    def _calc_b_wat_m3m3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_fvf_brine_Spivey_m3m3(self.t_k, self.p_mpa, self.s_ppm)

    def _calc_mu_wat_cp(self, number_cor):
        if number_cor == 0:
            return PVT.unf_viscosity_brine_MaoDuan_cP(self.t_k, self.p_mpa, self.s_ppm)

    def _calc_rs_wat_m3m3(self, number_cor):
        if number_cor == 0:
            return PVT.unf_gwr_brine_Spivey_m3m3(self.s_ppm, self.z)

    def _calc_heatcap_wat_jkgc(self, number_cor):
        if number_cor == 0:
            return PVT.unf_heat_capacity_water_IAPWS_JkgC(self.t_c)

    def _calc_thermal_conduct_wat_wmk(self, number_cor):
        if number_cor == 0:
            return PVT.unf_thermal_conductivity_water_IAPWS_WmC(self.t_c)

    def _calc_thermal_expansion_wat_1c(self, number_cor):
        if number_cor == 0:
            return PVT.unf_thermal_expansion_coefficient_water_IAPWS_1C(self.t_c)

    def _calc_sigma_oil_gas_Nm(self, number_cor):
        if number_cor == 0:
            return PVT.unf_surface_tension_go_Baker_Swerdloff_Nm(self.t_k, self.gamma_oil, self.p_mpa)
        if number_cor == 1:
            return PVT.unf_surface_tension_go_Abdul_Majeed_Nm(self.t_k, self.gamma_oil, self.rs_m3m3)

    def _calc_sigma_wat_gas_Nm(self, number_cor):
        if number_cor == 0:
            return PVT.unf_surface_tension_gw_Sutton_Nm(self.rho_wat_kgm3, self.rho_gas_kgm3, self.t_c)
        # TODO разобраться при использовании давления: когда идет калибровка давление изменяется - проверить где истинное где нет
        #   и давление при калибровке для всех единое, либо измененное только для свойств нефти
    def calc(self, p_bar, t_c):
        self.p_bar = p_bar
        self.t_c = t_c
        self.t_k = uc.c2k(self.t_c)
        self.p_mpa = uc.bar2MPa(self.p_bar)

        # oil
        # давление насыщения нефти
        self.pb_mpa = self._calc_pb_MPaa(self.option.pb_cor_number)
        self.pb_bar = uc.MPa2bar(self.pb_mpa)
        pbcal_MPaa = uc.bar2MPa(self.pb_cal_bar)
        if pbcal_MPaa > 0:
            p_fact = self.pb_mpa / pbcal_MPaa
            # сдвигаем шкалу по давлению для расчета, если задана калибровка
            self.p_mpa = p_fact * self.p_mpa
            self.pb_bar = self.pb_bar / p_fact
        # газосодержание
        self.rs_m3m3 = self._calc_rs_m3m3(self.option.rs_cor_number)
        # коэффициент изотермической сжимаемости
        self.compr_oil_1mpa = self._calc_compr_oil_1mpa(self.option.compr_oil_cor_number)
        self.compr_oil_1bar = uc.compr_1mpa_2_1bar(self.compr_oil_1mpa)
        # объемный коэффициент
        self.b_oil_b_m3m3 = self._calc_b_oil_in_pb_m3m3(self.option.b_oil_in_pb_cor_number)
        if self.p_mpa > self.pb_mpa:
            self.b_oil_m3m3 = self._calc_b_oil_above_pb_m3m3(self.option.b_oil_above_pb_cor_number)
        else:
            self.b_oil_m3m3 = self._calc_b_oil_below_pb_m3m3(self.option.b_oil_below_pb_cor_number)
        if self.b_oil_b_cal_m3m3 > 0:
            b_fact = (self.b_oil_b_cal_m3m3 - 1) / (self.b_oil_b_m3m3 - 1)
            self.b_oil_m3m3 = b_fact * self.b_oil_m3m3
        # плотность нефти
        self.rho_oil_kgm3 = self._calc_rho_oil_kgm3(self.option.rho_oil_cor_number)
        # вязкость
        self.mu_dead_oil_cp = self._calc_mu_dead_oil_cp(self.option.mu_dead_oil_cor_number)
        self.mu_oil_b_cP = self._calc_mu_oil_in_pb_cp(self.option.mu_oil_pb_cor_number)
        self.mu_oil_cp = self._calc_mu_oil_any_p_cp(self.option.mu_oil_any_p_cor_number)
        if self.mu_oil_b_cal_cp > 0:
            mu_fact = self.mu_oil_b_cal_cp / self.mu_oil_b_cP
            self.mu_oil_cp = mu_fact * self.mu_oil_cp
        # теплоемкость
        self.heatcap_oil_jkgc = self._calc_heatcap_oil_jkgc(self.option.heatcap_oil_cor_number)
        # теплопроводность
        self.thermal_conduct_oil_wmk = self._calc_thermal_conduct_oil_wmk(self.option.thermal_conduct_oil_cor_number)

        # gas
        self.tpc_k = self._calc_pseudocritical_temperature_k(self.option.pseudocritical_temperature_cor_number)
        self.ppc_mpa = self._calc_pseudocritical_pressure_mpa(self.option.pseudocritical_pressure_cor_number)
        self.z = self._calc_zfactor(self.option.z_cor_number)
        self.mu_gas_cp = self._calc_mu_gas_cp(self.option.mu_gas_cor_number)
        self.b_gas_m3m3 = self._calc_b_gas_m3m3(self.option.b_gas_cor_number)
        self.compr_gas_1bar = self._calc_compr_gas_1bar(self.option.compr_gas_cor_number)
        self.rho_gas_kgm3 = self._calc_rho_gas_kgm3(self.option.rho_gas_cor_number)
        self.heatcap_gas_jkgc = self._calc_heatcap_gas_jkgc(self.option.heatcap_gas_cor_number)
        self.thermal_conduct_gas_wmk = self._calc_thermal_conduct_gas_wmk(self.option.thermal_conduct_gas_cor_number)

        # water
        self.rho_wat_kgm3 = self._calc_rho_wat_kgm3(self.option.rho_wat_cor_number)
        self.compr_wat_1bar = self._calc_compr_wat_1bar(self.option.compr_gas_cor_number)
        self.b_wat_m3m3 = self._calc_b_wat_m3m3(self.option.b_wat_cor_number)
        self.mu_wat_cp = self._calc_mu_wat_cp(self.option.mu_wat_cor_number)
        self.rsw_m3m3 = self._calc_rs_wat_m3m3(self.option.rs_wat_cor_number)
        self.heatcap_wat_jkgc = self._calc_heatcap_wat_jkgc(self.option.heatcap_wat_cor_number)
        self.thermal_conduct_wat_wmk = self._calc_thermal_conduct_wat_wmk(self.option.thermal_conduct_wat_cor_number)
        self.thermal_expansion_wat_1c = self._calc_thermal_expansion_wat_1c(self.option.thermal_expansion_wat_cor_number)

        # some system properties
        self.sigma_oil_gas_Nm = self._calc_sigma_oil_gas_Nm(self.option.sigma_oil_gas_cor_number)
        self.sigma_wat_gas_Nm = self._calc_sigma_wat_gas_Nm(self.option.sigma_wat_gas_cor_number)

