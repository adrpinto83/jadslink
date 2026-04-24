include $(TOPDIR)/rules.mk

PKG_NAME:=jadslink-agent
PKG_VERSION:=1.0.0
PKG_RELEASE:=1

PKG_SOURCE:=$(PKG_NAME)-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://github.com/adrpinto83/jadslink/releases/download/v$(PKG_VERSION)/
PKG_HASH:=skip

PKG_MAINTAINER:=JADS Studio <info@jads.studio>
PKG_LICENSE:=Proprietary
PKG_LICENSE_FILES:=LICENSE

include $(INCLUDE_DIR)/package.mk

define Package/jadslink-agent
  SECTION:=net
  CATEGORY:=Network
  TITLE:=JADSlink Field Agent
  DESCRIPTION:=Satellite connectivity field agent for OpenWrt routers
  DEPENDS:=+python3 +python3-requests +python3-schedule +tc +kmod-ifb +kmod-sched-core +kmod-sched-htb +iptables-mod-conntrack-extra
  USERID:=jadslink=888:jadslink=888
endef

define Package/jadslink-agent/description
  JADSlink Field Agent is a lightweight Python application that runs on
  OpenWrt routers to provide captive portal authentication, bandwidth
  limiting, and ticket validation for satellite internet connectivity.

  Features:
  - Lightweight: < 25MB RAM, < 5% CPU idle
  - Offline operation: Local SQLite cache
  - Auto-detection: Automatic network interface discovery
  - Bandwidth limiting: tc-based QoS with HTB
  - Firewall: iptables with persistent rules
  - Portal: Embedded HTML captive portal < 40KB
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	cp -r $(TOPDIR)/feeds/custom/jadslink-agent/files/* $(PKG_BUILD_DIR)/
endef

define Build/Compile
	# No compilation needed, Python application
endef

define Package/jadslink-agent/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/usr/bin/jadslink-agent $(1)/usr/bin/

	$(INSTALL_DIR) $(1)/usr/lib/jadslink
	$(CP) $(PKG_BUILD_DIR)/usr/lib/jadslink/* $(1)/usr/lib/jadslink/

	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/etc/init.d/jadslink $(1)/etc/init.d/

	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/etc/config/jadslink $(1)/etc/config/

	$(INSTALL_DIR) $(1)/var/lib/jadslink
	$(INSTALL_DIR) $(1)/etc
endef

define Package/jadslink-agent/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	echo ""
	echo "JADSlink Agent installation complete!"
	echo ""
	echo "Next steps:"
	echo "1. Configure the agent: uci set jadslink.agent.api_key='YOUR_API_KEY'"
	echo "2. Set the node ID: uci set jadslink.agent.node_id='YOUR_NODE_ID'"
	echo "3. Commit changes: uci commit jadslink"
	echo "4. Start the service: /etc/init.d/jadslink start"
	echo "5. Enable on boot: /etc/init.d/jadslink enable"
	echo "6. Check logs: logread -f | grep jadslink"
	echo ""
fi
endef

define Package/jadslink-agent/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	/etc/init.d/jadslink stop
	/etc/init.d/jadslink disable
fi
endef

$(eval $(call BuildPackage,jadslink-agent))
