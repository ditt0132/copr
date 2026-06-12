{% include rust2rpm_target ~ "-header.spec.inc" ignore missing %}
# Created based on rust2rpm 
{% if rpm_bcond_check == 0 %}
{% for comment in rpm_bcond_check_comments %}
{{ comment }}
{% endfor %}
{% endif %}
%bcond check {{ rpm_bcond_check }}
{% if not (rpm_binary_package or rpm_cdylib_package) or not cargo_install_bin %}
%global debug_package %{nil}
{% endif %}
{% if build_rustflags_debuginfo %}

# build with reduced debuginfo to work around memory limits
%global rustflags_debuginfo {{ build_rustflags_debuginfo }}
{% endif %}

{% if not cargo_install_lib %}
# prevent library files from being installed
%global cargo_install_lib 0

{% endif %}
{% if not cargo_install_bin %}
# prevent executables from being installed
%global cargo_install_bin 0

{% endif %}
%global crate {{ crate_name }}
{% if crate_version != rpm_version %}
%global crate_version {{ crate_version }}
{% endif %}
{% if conf_supported_arches %}

# compile and run tests only on supported architectures
%global supported_arches {{ conf_supported_arches }}
{% endif %}
{% if conf_unsupported_arches %}

# compile and run tests only on supported architectures
%global unsupported_arches {{ conf_unsupported_arches }}
{% endif %}

Name:           {{ rpm_name }}
Version:        {{ rpm_version }}
Release:        {{ rpm_release }}
Summary:        {{ rpm_summary }}
{% if rpm_group %}
Group:          {{ rpm_group }}
{% endif %}

{% if crate_license != rpm_license %}
# Upstream license specification: {{ crate_license|default("(missing)") }}
{% endif %}
License:        {{ rpm_license|default("# FIXME") }}
{% if rpm_license_comments is not none %}
{{ rpm_license_comments }}
{% endif %}
URL:            {{ rpm_url }}
{% if crate_version != rpm_version %}
Source:         %{crates_source %{crate} %{crate_version}}
{% else %}
Source:         %{crates_source}
{% endif %}
{% if rpm_vendor_source %}
Source:         {{ rpm_vendor_source }}
{% endif %}
{% for source in rpm_extra_sources %}
{% for comment_line in source.comment_lines %}
{{ comment_line }}
{% endfor %}
Source{{ source.number }}:{{ source.whitespace }}{{ source.file }}
{% endfor %}
{% if rpm_patch_file_automatic is not none %}
# Automatically generated patch to strip dependencies and normalize metadata
Patch:          {{ rpm_patch_file_automatic }}
{% endif %}
{% if rpm_patch_file_manual is not none %}
{% if rust2rpm_target == "opensuse" %}
# PATCH-FIX-OPENSUSE {{ rpm_patch_file_manual }} — Manually created patch for downstream crate metadata changes
{% else %}
# Manually created patch for downstream crate metadata changes
{% endif %}
{% for comment_line in rpm_patch_file_comments %}
{{ comment_line }}
{% endfor %}
Patch:          {{ rpm_patch_file_manual }}
{% endif %}
{% for patch in rpm_extra_patches %}
{% for comment_line in patch.comment_lines %}
{{ comment_line }}
{% endfor %}
Patch{{ patch.number }}:{{ patch.whitespace }}{{ patch.file }}
{% endfor %}

{% if rpm_build_arch_noarch %}
BuildArch:      noarch

{% endif %}
{% if rpm_exclusivearch %}
ExclusiveArch:  %{rust_arches}

{% endif %}
BuildRequires:  {{ rust_packaging_dep }}
{% if include_build_requires and rpm_vendor_source is none %}
  {% for req in rpm_buildrequires %}
BuildRequires:  {{ req }}
  {% endfor %}
  {% if rpm_test_requires|length > 0 %}
%if %{with check}
    {% for req in rpm_test_requires %}
BuildRequires:  {{ req }}
    {% endfor %}
%endif
  {% endif %}
{% endif %}
  {% for req in conf_buildrequires %}
BuildRequires:  {{ req }}
  {% endfor %}
  {% if conf_test_requires %}
%if %{with check}
  {% for req in conf_test_requires %}
BuildRequires:  {{ req }}
  {% endfor %}
%endif
  {% endif %}

%global _description %{expand:
{% if rpm_description is none %}
%{summary}.
{%- else %}
{{ rpm_description }}
{%- endif %}
}

%description %{_description}

{% if (rpm_binary_package or rpm_cdylib_package) and cargo_install_bin %}
%package     -n {{ rpm_binary_package_name }}
Summary:        %{summary}
  {% if rpm_group %}
Group:          # FIXME
  {% endif %}
# FIXME: paste output of %%cargo_license_summary here
License:        # FIXME
# LICENSE.dependencies contains a full license breakdown
  {% for req in conf_bin_requires %}
Requires:       {{ req }}
  {% endfor %}

{% if rpm_binary_package_extra is not none %}
{{ rpm_binary_package_extra }}
{% endif -%}

%description -n {{ rpm_binary_package_name }} %{_description}

%files       -n {{ rpm_binary_package_name }}
  {% if rpm_license_files|length > 0 %}
    {% for file in rpm_license_files %}
%license {{ file }}
    {% endfor %}
  {% else %}
# FIXME: no license files detected
  {% endif %}
%license LICENSE.dependencies
{% if rpm_vendor_source is not none %}
%license cargo-vendor.txt
{% endif %}
  {% for file in rpm_doc_files %}
%doc {{ file }}
  {% endfor %}
  {% for bin in rpm_binary_names %}
%{_bindir}/{{ bin }}
  {% endfor %}
  {% for file in rpm_extra_files %}
{{ file }}
  {% endfor %}

{% endif -%}

{% if rpm_package_extra is not none %}
{{ rpm_package_extra }}
{% endif -%}

{% if rpm_library_package and cargo_install_lib %}
  {% for feature in crate_features %}
    {% if feature is none %}
      {% set pkg = "   devel" %}
      {% set conf_prefix = "lib" %}
    {% else %}
      {% set pkg = "-n %%{name}+%s-devel"|format(feature) %}
      {% set conf_prefix = "lib+%s"|format(feature) %}
    {% endif %}
%package     {{ pkg }}
Summary:        %{summary}
BuildArch:      noarch
    {% if include_provides %}
Provides:       {{ rpm_provides.get(feature) }}
    {% endif %}
    {% if include_requires %}
      {% for req in rpm_requires.get(feature) %}
Requires:       {{ req }}
      {% endfor %}
    {% endif %}
    {% for req in conf_lib_requires.get(conf_prefix) %}
Requires:       {{ req }}
    {% endfor %}

%description {{ pkg }} %{_description}

This package contains library source intended for building other packages which
use {% if feature is not none %}the "{{ feature }}" feature of {% endif %}the "%{crate}" crate.

%files       {{ pkg }}
    {% if feature is none %}
      {% if rpm_license_files|length > 0 %}
        {% for file in rpm_license_files %}
%license %{crate_instdir}/{{ file }}
        {% endfor %}
      {% else %}
# FIXME: no license files detected
      {% endif %}
      {% for file in rpm_doc_files %}
%doc %{crate_instdir}/{{ file }}
      {% endfor %}
%{crate_instdir}/
      {% for file in rpm_exclude_crate_files %}
%exclude %{crate_instdir}/{{ file }}
      {% endfor %}
    {% else %}
%ghost %{crate_instdir}/Cargo.toml
    {% endif %}

  {% endfor %}
{% endif -%}

%prep
{% if crate_version != rpm_version %}
%autosetup -n %{crate}-%{crate_version} -p1{{ rpm_autosetup_args}}
{% else %}
%autosetup -n %{crate}-%{version} -p1{{ rpm_autosetup_args}}
{% endif %}
{% for command in rpm_prep_pre %}
{{ command }}
{% endfor %}
%cargo_prep{{ cargo_prep_args }}
{% for command in rpm_prep_post %}
{{ command }}
{% endfor %}

{% if not include_build_requires and not rpm_vendor_source is not none %}
%generate_buildrequires
{% for command in rpm_genbr_pre %}
{{ command }}
{% endfor %}
%cargo_generate_buildrequires{{ cargo_args }}
{% for command in rpm_genbr_post %}
{{ command }}
{% endfor %}

{% endif %}
%build
{% for command in rpm_build_pre %}
{{ command }}
{% endfor %}
{% if conf_supported_arches %}
%ifarch %{supported_arches}
{% endif %}
{% if conf_unsupported_arches %}
%ifnarch %{unsupported_arches}
{% endif %}
%cargo_build{{ cargo_args }}
{% if conf_supported_arches %}
%endif
{% endif %}
{% if conf_unsupported_arches %}
%endif
{% endif %}
{% if (rpm_binary_package or rpm_cdylib_package) and cargo_install_bin %}
%{cargo_license_summary{{ cargo_args }}}
%{cargo_license{{ cargo_args }}} > LICENSE.dependencies
{% endif %}
{% if rpm_vendor_source is not none %}
%{cargo_vendor_manifest}
{% endif %}
{% for command in rpm_build_post %}
{{ command }}
{% endfor %}

%install
{% for command in rpm_install_pre %}
{{ command }}
{% endfor %}
{% if rpm_cdylib_package and (rpm_library_package or rpm_binary_package) %}
%cargo_install{{ cargo_args }}
{% if not conf_suppress_cdylib_install_fixme %}
# FIXME: install shared library
{% endif %}
{% elif rpm_cdylib_package %}
{% if not conf_suppress_cdylib_install_fixme %}
# FIXME: install shared library
{% endif %}
{% else %}
%cargo_install{{ cargo_args }}
{% for rpm_bin_rename in rpm_bin_renames %}
{{ rpm_bin_rename }}
{% endfor %}
{% endif %}
{% for command in rpm_install_post %}
{{ command }}
{% endfor %}

%if %{with check}
{% if conf_supported_arches %}
%ifarch %{supported_arches}
{% endif %}
{% if conf_unsupported_arches %}
%ifnarch %{unsupported_arches}
{% endif %}
%check
{% for command in rpm_check_pre %}
{{ command }}
{% endfor %}
{% if cargo_test_commands %}
{% for command in cargo_test_commands %}
{{ command }}
{% endfor %}
{% else %}
%cargo_test{{ cargo_args }}
{% endif %}
{% if conf_supported_arches %}
%endif
{% endif %}
{% if conf_unsupported_arches %}
%endif
{% endif %}
{% for command in rpm_check_post %}
{{ command }}
{% endfor %}
%endif

%changelog
{% if use_rpmautospec %}
%autochangelog
{%- else %}
{%- if make_changelog_entry -%}

  {% include rust2rpm_target ~ "-changelog.spec.inc" %}
{% endif %}
{% endif %}
