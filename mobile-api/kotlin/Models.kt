package com.jadsstudio.jadslink.data.remote

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * Modelos de datos de la API de operador de JADSLink.
 * Generados a partir del contrato verificado (openapi.yaml, 2026-07-08).
 *
 * Usan Moshi. Los campos que la API omite a veces se declaran nullable con
 * default para tolerar respuestas parciales.
 */

// ─────────────────────────── AUTH ───────────────────────────

@JsonClass(generateAdapter = true)
data class LoginPayload(
    val username: String,
    val password: String,
)

@JsonClass(generateAdapter = true)
data class SignupPayload(
    @Json(name = "company_name") val companyName: String,
    val username: String,
    val password: String,
    val email: String = "",
    @Json(name = "contact_phone") val contactPhone: String = "",
)

@JsonClass(generateAdapter = true)
data class ChangePasswordPayload(
    @Json(name = "current_password") val currentPassword: String,
    @Json(name = "new_password") val newPassword: String,
)

@JsonClass(generateAdapter = true)
data class AuthResult(
    val token: String,
    val username: String,
    val role: String,
    @Json(name = "account_id") val accountId: String,
)

@JsonClass(generateAdapter = true)
data class ChangePasswordResult(
    val ok: Boolean,
    val token: String,
)

// ─────────────────────────── CUENTA / PLAN ───────────────────────────

@JsonClass(generateAdapter = true)
data class Me(
    val username: String,
    val email: String? = null,
    @Json(name = "full_name") val fullName: String? = null,
    val role: String,
    @Json(name = "account_id") val accountId: String,
    val account: Account? = null,
)

@JsonClass(generateAdapter = true)
data class Account(
    val id: String,
    val name: String,
    val slug: String,
    val status: String,          // trial | active | past_due | suspended
    val plan: String,
    val usage: Usage? = null,
    val billing: Billing? = null,
)

@JsonClass(generateAdapter = true)
data class Usage(
    val plan: String,
    @Json(name = "plan_name") val planName: String,
    @Json(name = "device_count") val deviceCount: Int,
    @Json(name = "included_devices") val includedDevices: Int,
    @Json(name = "max_devices") val maxDevices: Int? = null,
    @Json(name = "extra_devices") val extraDevices: Int,
    @Json(name = "base_price") val basePrice: Double,
    @Json(name = "price_per_extra_device") val pricePerExtraDevice: Double,
    @Json(name = "extra_cost") val extraCost: Double,
    @Json(name = "total_monthly") val totalMonthly: Double,
    @Json(name = "at_limit") val atLimit: Boolean,
    @Json(name = "tickets_per_month") val ticketsPerMonth: Int,
    @Json(name = "tickets_used") val ticketsUsed: Int,
    @Json(name = "tickets_bonus") val ticketsBonus: Int,
    @Json(name = "tickets_unlimited") val ticketsUnlimited: Boolean,
)

@JsonClass(generateAdapter = true)
data class Billing(
    @Json(name = "billing_cycle_end") val billingCycleEnd: String? = null,
    @Json(name = "days_left") val daysLeft: Int,
    val expired: Boolean,
    val grace: Boolean,
)

@JsonClass(generateAdapter = true)
data class Plan(
    val key: String,
    val name: String,
    @Json(name = "base_price_usd") val basePriceUsd: Double,
    @Json(name = "included_devices") val includedDevices: Int,
    @Json(name = "price_per_extra_device_usd") val pricePerExtraDeviceUsd: Double,
    @Json(name = "max_devices") val maxDevices: Int? = null,
    val features: Map<String, Any?> = emptyMap(),
)

@JsonClass(generateAdapter = true)
data class AccountUser(
    val id: String,
    val username: String,
    val email: String? = null,
    @Json(name = "full_name") val fullName: String? = null,
    val role: String,            // owner | manager | viewer
    @Json(name = "is_active") val isActive: Boolean = true,
)

@JsonClass(generateAdapter = true)
data class Quota(
    val plan: String,
    val limit: Int,
    val used: Int,
    val bonus: Int,
    val available: Int,
    val unlimited: Boolean,
    @Json(name = "reset_at") val resetAt: String? = null,
)

// ─────────────────────────── DASHBOARD ───────────────────────────

@JsonClass(generateAdapter = true)
data class Overview(
    @Json(name = "devices_total") val devicesTotal: Int,
    @Json(name = "devices_online") val devicesOnline: Int,
    @Json(name = "active_clients") val activeClients: Int,
    @Json(name = "active_codes") val activeCodes: Int,
    @Json(name = "recent_connections") val recentConnections: List<Map<String, Any?>> = emptyList(),
)

// ─────────────────────────── GATEWAYS ───────────────────────────

@JsonClass(generateAdapter = true)
data class Device(
    val id: String,
    val name: String,
    val location: String = "",
    val model: String = "",
    val online: Boolean = false,
    @Json(name = "last_seen") val lastSeen: String? = null,
    val firmware: String = "",
    val config: Map<String, Any?> = emptyMap(),
    @Json(name = "api_key") val apiKey: String? = null,
    @Json(name = "account_id") val accountId: String? = null,
    @Json(name = "group_id") val groupId: Int? = null,
    @Json(name = "active_clients") val activeClients: Int = 0,
)

@JsonClass(generateAdapter = true)
data class DeviceRegister(
    val name: String,
    val location: String = "",
    val model: String = "OpenWrt",
    @Json(name = "group_id") val groupId: Int? = null,
)

@JsonClass(generateAdapter = true)
data class DeviceActivate(
    @Json(name = "activation_code") val activationCode: String,
    val name: String,
    val location: String = "",
)

@JsonClass(generateAdapter = true)
data class DeviceUpdate(
    val name: String? = null,
    val location: String? = null,
    @Json(name = "group_id") val groupId: Int? = null,
)

@JsonClass(generateAdapter = true)
data class DeviceCredentials(
    @Json(name = "device_id") val deviceId: String,
    @Json(name = "api_key") val apiKey: String,
    @Json(name = "serial_number") val serialNumber: String? = null,
    val activated: Boolean = false,
)

@JsonClass(generateAdapter = true)
data class ConfigUpdate(
    val config: Map<String, Any?>,
)

@JsonClass(generateAdapter = true)
data class SsidUpdate(
    val ssid: String,
)

@JsonClass(generateAdapter = true)
data class ConnectedClient(
    val mac: String = "",
    val ip: String = "",
    val hostname: String = "",
    @Json(name = "bytes_in") val bytesIn: Long = 0,
    @Json(name = "bytes_out") val bytesOut: Long = 0,
    @Json(name = "code_used") val codeUsed: String = "",
    val active: Boolean = true,
)

@JsonClass(generateAdapter = true)
data class Report(
    val timestamp: String? = null,
    @Json(name = "clients_count") val clientsCount: Int = 0,
    @Json(name = "bytes_in") val bytesIn: Long = 0,
    @Json(name = "bytes_out") val bytesOut: Long = 0,
    @Json(name = "cpu_load") val cpuLoad: Double = 0.0,
    @Json(name = "mem_free_mb") val memFreeMb: Double = 0.0,
    @Json(name = "uptime_sec") val uptimeSec: Long = 0,
    @Json(name = "wan_ip") val wanIp: String = "",
)

// ─────────────────────────── CÓDIGOS ───────────────────────────

@JsonClass(generateAdapter = true)
data class CodeCreate(
    val quantity: Int = 1,       // OJO: la API espera "quantity", no "count"
    @Json(name = "duration_min") val durationMin: Int = 60,
    @Json(name = "max_uses") val maxUses: Int = 1,
    @Json(name = "bandwidth_dn") val bandwidthDn: Int = 0,
    @Json(name = "bandwidth_up") val bandwidthUp: Int = 0,
    @Json(name = "expires_hours") val expiresHours: Int? = null,
    val note: String = "",
    val prefix: String = "",
)

@JsonClass(generateAdapter = true)
data class CodeCreateResult(
    val created: Int,
    val codes: List<String>,
    val quota: Quota? = null,
)

@JsonClass(generateAdapter = true)
data class Code(
    val id: Int,
    val code: String,
    @Json(name = "duration_min") val durationMin: Int = 0,
    @Json(name = "max_uses") val maxUses: Int = 1,
    @Json(name = "used_count") val usedCount: Int = 0,
    val status: String = "",
    val note: String = "",
    @Json(name = "created_at") val createdAt: String? = null,
    @Json(name = "expires_at") val expiresAt: String? = null,
)

// ─────────────────────────── TIENDA / VENTAS ───────────────────────────

@JsonClass(generateAdapter = true)
data class Product(
    val id: Int,
    val name: String,
    @Json(name = "duration_min") val durationMin: Int,
    @Json(name = "price_usd") val priceUsd: Double,
    @Json(name = "price_ves") val priceVes: Double,
    @Json(name = "bandwidth_dn") val bandwidthDn: Int = 0,
    @Json(name = "bandwidth_up") val bandwidthUp: Int = 0,
    @Json(name = "is_active") val isActive: Boolean = true,
    @Json(name = "sort_order") val sortOrder: Int = 0,
)

@JsonClass(generateAdapter = true)
data class ProductCreate(
    val name: String,
    @Json(name = "duration_min") val durationMin: Int = 60,
    @Json(name = "price_usd") val priceUsd: Double = 0.0,
    @Json(name = "price_ves") val priceVes: Double = 0.0,
    @Json(name = "bandwidth_dn") val bandwidthDn: Int = 0,
    @Json(name = "bandwidth_up") val bandwidthUp: Int = 0,
    @Json(name = "sort_order") val sortOrder: Int = 0,
)

@JsonClass(generateAdapter = true)
data class ProductUpdate(
    val name: String? = null,
    @Json(name = "duration_min") val durationMin: Int? = null,
    @Json(name = "price_usd") val priceUsd: Double? = null,
    @Json(name = "price_ves") val priceVes: Double? = null,
    @Json(name = "bandwidth_dn") val bandwidthDn: Int? = null,
    @Json(name = "bandwidth_up") val bandwidthUp: Int? = null,
    @Json(name = "is_active") val isActive: Boolean? = null,
    @Json(name = "sort_order") val sortOrder: Int? = null,
)

@JsonClass(generateAdapter = true)
data class Order(
    val id: Int,
    val token: String? = null,
    val status: String,          // pending | approved | rejected
    @Json(name = "device_id") val deviceId: String? = null,
    @Json(name = "device_name") val deviceName: String = "",
    @Json(name = "product_name") val productName: String = "",
    @Json(name = "duration_min") val durationMin: Int = 0,
    @Json(name = "price_usd") val priceUsd: Double = 0.0,
    val method: String = "",
    val reference: String = "",
    @Json(name = "buyer_name") val buyerName: String = "",
    @Json(name = "buyer_phone") val buyerPhone: String = "",
    val code: String = "",
    @Json(name = "review_note") val reviewNote: String = "",
    @Json(name = "created_at") val createdAt: String? = null,
    @Json(name = "reviewed_at") val reviewedAt: String? = null,
)

@JsonClass(generateAdapter = true)
data class RejectPayload(
    val note: String = "",
)

// ─────────────────────────── PAGOS ───────────────────────────

@JsonClass(generateAdapter = true)
data class Payment(
    val id: Int,
    @Json(name = "account_id") val accountId: String,
    @Json(name = "account_name") val accountName: String = "",
    @Json(name = "amount_usd") val amountUsd: Double,
    val method: String,
    val reference: String = "",
    val note: String = "",
    @Json(name = "proof_file") val proofFile: String = "",
    val status: String,          // pending | approved | rejected
    @Json(name = "created_at") val createdAt: String? = null,
)

// ─────────────────────────── EXTRAS ───────────────────────────

@JsonClass(generateAdapter = true)
data class ExchangeRate(
    val rate: Double,
    val source: String = "",
    @Json(name = "updated_at") val updatedAt: String? = null,
    val cached: Boolean = false,
)

@JsonClass(generateAdapter = true)
data class Group(
    val id: Int,
    val name: String,
    @Json(name = "account_id") val accountId: String? = null,
)

@JsonClass(generateAdapter = true)
data class GroupCreate(
    val name: String,
)

@JsonClass(generateAdapter = true)
data class SimpleOk(
    val ok: Boolean = true,
)
