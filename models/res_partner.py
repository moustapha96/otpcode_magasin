# # -*- coding: utf-8 -*-
# from odoo import models, fields, api
# from datetime import timedelta
# import random

# class ResPartner(models.Model):
#     _inherit = 'res.partner'

#     otp_verified = fields.Boolean(string='OTP vérification', default=False)
#     otp_code_ids = fields.One2many('otp.code', 'partner_id', string="Codes OTP")

#     # ---------- Utils ----------
#     def _purge_partner_otps(self):
#         """Supprime tous les OTP pour ce partenaire."""
#         for partner in self:
#             self.env['otp.code'].sudo().search([('partner_id', '=', partner.id)]).unlink()

#     def _make_otp(self, ttl_minutes=30):
#         """Crée un OTP (4 chiffres) avec expiration, sans envoi."""
#         self.ensure_one()
#         otp_code = ''.join(random.choices('0123456789', k=4))
#         expiration = fields.Datetime.now() + timedelta(minutes=ttl_minutes)
#         rec = self.env['otp.code'].sudo().create({
#             'partner_id': self.id,
#             'code': otp_code,
#             'expiration': expiration,
#         })
#         return rec

#     # ---------- Voir le code (debug/outillage) ----------
#     def get_otp(self):
#         """Renvoie un OTP valide si existant, sinon purge et recrée."""
#         self.ensure_one()
#         existing = self.env['otp.code'].sudo().search([
#             ('partner_id', '=', self.id),
#             ('expiration', '>', fields.Datetime.now())
#         ], limit=1, order="expiration desc")
#         if existing:
#             return existing.code
#         # Sinon purge + recrée
#         self._purge_partner_otps()
#         if self.phone or self.mobile:
#             rec = self._make_otp(ttl_minutes=30)
#             return rec.code
#         return False

#     # ---------- Génération + envoi ----------
#     def send_otp(self):
#         """Purge, génère nouveau code, envoie par SMS, retourne le code (pour logs)."""
#         for partner in self:
#             partner._purge_partner_otps()
#             rec = partner._make_otp(ttl_minutes=30)
#             otp_code = rec.code

#             phone = partner.mobile or partner.phone
#             message_sms = (
#                 f"Bonjour,\n"
#                 f"Votre code de vérification est {otp_code}\n"
#                 f"Merci de ne pas répondre à ce message.\n"
#                 f"Equipe CCTS"
#             )
#             if phone:
#                 self.send_sms(phone, message_sms)
#             # Retourne pour logs (NE PAS exposer au client)
#             return otp_code

#     # ---------- Vérification ----------
#     def verify_otp(self, otp_code):
#         """Vérifie l'OTP et purge tous les OTP du partner si succès."""
#         self.ensure_one()
#         otp_rec = self.env['otp.code'].sudo().search([
#             ('partner_id', '=', self.id),
#             ('code', '=', str(otp_code)),
#             ('expiration', '>', fields.Datetime.now()),
#         ], limit=1)

#         if not otp_rec:
#             # purge des expirés optionnelle
#             self.env['otp.code'].sudo().search([
#                 ('partner_id', '=', self.id),
#                 ('expiration', '<=', fields.Datetime.now()),
#             ]).unlink()
#             return False

#         # succès
#         self.write({'otp_verified': True, 'is_verified': True})
#         self._purge_partner_otps()
#         return True

#     # ---------- Envoi SMS ----------
#     @api.model
#     def send_sms(self, recipient, message):
#         """Envoie SMS via send.sms (adapté à ton module)."""
#         sms_record = self.env['send.sms'].sudo().create({
#             'recipient': recipient,
#             'message': message,
#         })
#         return sms_record.send_sms()


# class OtpCode(models.Model):  # <-- persistant (pas Transient) pour audit si besoin
#     _name = 'otp.code'
#     _description = 'OTP Code'

#     partner_id = fields.Many2one('res.partner', string='Partner', required=True, index=True, ondelete='cascade')
#     code = fields.Char(string='OTP Code', required=True, index=True)
#     expiration = fields.Datetime(string='Expiration', required=True, index=True)

#     _sql_constraints = [
#         ('otp_code_len', "CHECK (char_length(code)=4)", "Code OTP invalide (4 chiffres)."),
#     ]

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta
import random

class ResPartner(models.Model):
    _inherit = 'res.partner'

    otp_verified = fields.Boolean(string='OTP vérification', default=False)
    otp_code_ids = fields.One2many('otp.code', 'partner_id', string="Codes OTP")

    # ---------- Utils ----------
    def _purge_partner_otps(self):
        """Helper privé: supprime tous les OTP pour ce partenaire."""
        for partner in self:
            self.env['otp.code'].sudo().search([('partner_id', '=', partner.id)]).unlink()

    def purge_partner_otps(self):
        """
        Action bouton (publique) appelée par la vue.
        Doit exister pour éviter 'n'est pas une action valide'.
        """
        self._purge_partner_otps()
        # Optionnel: message feedback en chatter
        for p in self:
            p.message_post(body="Tous les OTP de ce partenaire ont été purgés.")
        return True

    def _make_otp(self, ttl_minutes=30):
        self.ensure_one()
        otp_code = ''.join(random.choices('0123456789', k=4))
        expiration = fields.Datetime.now() + timedelta(minutes=ttl_minutes)
        rec = self.env['otp.code'].sudo().create({
            'partner_id': self.id,
            'code': otp_code,
            'expiration': expiration,
        })
        return rec

    def get_otp(self):
        self.ensure_one()
        existing = self.env['otp.code'].sudo().search([
            ('partner_id', '=', self.id),
            ('expiration', '>', fields.Datetime.now())
        ], limit=1, order="expiration desc")
        if existing:
            return existing.code
        self._purge_partner_otps()
        if self.phone or self.mobile:
            rec = self._make_otp(ttl_minutes=30)
            return rec.code
        return False

    def send_otp(self):
        for partner in self:
            partner._purge_partner_otps()
            rec = partner._make_otp(ttl_minutes=30)
            code = rec.code
            phone = partner.mobile or partner.phone
            if phone:
                message = (
                    f"Bonjour,\nVotre code de vérification est {code}\n"
                    f"Merci de ne pas répondre à ce message.\nEquipe CCTS"
                )
                self.send_sms(phone, message)
            return code

    def verify_otp(self, otp_code):
        self.ensure_one()
        otp_rec = self.env['otp.code'].sudo().search([
            ('partner_id', '=', self.id),
            ('code', '=', str(otp_code)),
            ('expiration', '>', fields.Datetime.now()),
        ], limit=1)
        if not otp_rec:
            # # purge des expirés (optionnel)
            # self.env['otp.code'].sudo().search([
            #     ('partner_id', '=', self.id),
            #     ('expiration', '<=', fields.Datetime.now()),
            # ]).unlink()
            return False
        self.write({'otp_verified': True, 'is_verified': True})
        self._purge_partner_otps()
        return True

    @api.model
    def send_sms(self, recipient, message):
        sms = self.env['send.sms'].sudo().create({
            'recipient': recipient,
            'message': message,
        })
        return sms.send_sms()


class OtpCode(models.Model):  # garder un modèle persistant (pas transient) si tu veux voir l'historique
    _name = 'otp.code'
    _description = 'OTP Code'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, index=True, ondelete='cascade')
    code = fields.Char(string='OTP Code', required=True, index=True)
    expiration = fields.Datetime(string='Expiration', required=True, index=True)

    _sql_constraints = [
        ('otp_code_len', "CHECK (char_length(code)=4)", "Code OTP invalide (4 chiffres)."),
    ]
